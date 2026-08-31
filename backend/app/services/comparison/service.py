import asyncio
from dataclasses import dataclass
from typing import Optional

from app.providers.llm_gateway import LLMGateway, ChatRequest
from app.services.routing.router import ModelService
from app.services.context.budget import fit_messages_to_budget
from app.core.errors import AppError
from app.core.config import settings
from app.db.schema import UsageRecord


@dataclass
class ModelRunResult:
    model_id: str
    provider_id: str
    content: str = ""
    status: str = "pending"
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None


JUDGE_CRITERIA = ["correctness", "relevance", "completeness", "reasoning_quality", "code_quality", "instruction_following", "clarity"]

JUDGE_PROMPT_TEMPLATE = """You are an impartial AI response judge. Compare the following AI responses to the same task.

Task:
{task}

Responses:
{responses}

Score each response from 0 to 10 on: {criteria}.
Return ONLY valid JSON in this exact format:
{{"winner": "<model_id of the winner>", "scores": {{"<model_id>": <0-10 float>, ...}}, "reason": "<1-3 sentence explanation>"}}
Do not include any other text."""


class ComparisonService:
    def __init__(self, db, gateway: Optional[LLMGateway] = None):
        self.db = db
        self.gateway = gateway or LLMGateway()
        self.model_service = ModelService(db)

    async def run(self, user_id: str, content: str, model_ids: list[str], context_messages: list[dict] = None, conversation_id: str = None) -> dict:
        if not model_ids:
            raise AppError("INVALID_REQUEST", "No models selected", 422)
        if len(model_ids) > 6:
            raise AppError("INVALID_REQUEST", "Too many models (max 6)", 422)

        authorized_providers = await self.model_service.get_authorized_provider_ids(user_id)
        keys = await self._get_provider_keys(user_id)

        tasks = [self._run_single(model_id, content, context_messages, authorized_providers, keys) for model_id in model_ids]
        runs = await asyncio.gather(*tasks, return_exceptions=False)

        for r in runs:
            if r.status == "success":
                usage = UsageRecord(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    provider_id=r.provider_id,
                    model_id=r.model_id,
                    input_tokens=r.input_tokens,
                    output_tokens=r.output_tokens,
                )
                self.db.add(usage)

        winner, scores, reason = await self._judge(content, runs)

        return {
            "task": content,
            "runs": [self._run_to_dict(r) for r in runs],
            "winner": winner,
            "scores": scores,
            "reason": reason,
            "criteria": JUDGE_CRITERIA,
        }

    async def _run_single(self, model_id, content, context_messages, authorized_providers, keys) -> ModelRunResult:
        model = await self.model_service.get_model(model_id)
        if model.provider_id not in authorized_providers:
            return ModelRunResult(model_id=model_id, provider_id=model.provider_id, status="error",
                                  error_code="PROVIDER_UNAUTHORIZED", error_message="Provider not authorized")

        messages = list(context_messages or [])
        messages.append({"role": "user", "content": content})
        # Spec §7/§9: same task/context for every model, budgeted per model window.
        messages = fit_messages_to_budget(messages, model.context_window)
        api_key = keys.get(model.provider_id)

        request = ChatRequest(model_id=model_id, messages=messages, api_key=api_key, temperature=0.3)
        try:
            response = await self.gateway.chat(request)
            return ModelRunResult(
                model_id=model_id, provider_id=model.provider_id, content=response.content,
                status="success", latency_ms=response.latency_ms,
                input_tokens=response.input_tokens, output_tokens=response.output_tokens,
            )
        except AppError as e:
            return ModelRunResult(model_id=model_id, provider_id=model.provider_id, status="error",
                                  error_code=e.code, error_message=e.message)

    async def _get_provider_keys(self, user_id) -> dict:
        from app.services.credentials.service import CredentialsService
        return await CredentialsService(self.db).get_decrypted_keys(user_id)

    async def _judge(self, task, runs) -> tuple[Optional[str], dict, str]:
        successful = [r for r in runs if r.status == "success"]
        if not successful:
            return None, {r.model_id: 0.0 for r in runs}, "All models failed to respond."

        if len(successful) == 1:
            r = successful[0]
            return r.model_id, {r.model_id: 8.0}, "Only one model responded; no comparison needed."

        responses_text = "\n\n".join(f"--- {r.model_id} ---\n{r.content}" for r in successful)
        prompt = JUDGE_PROMPT_TEMPLATE.format(
            task=task, responses=responses_text, criteria=", ".join(JUDGE_CRITERIA)
        )

        judge_model = settings.judge_model
        judge_key = self._judge_key()
        request = ChatRequest(model_id=judge_model, messages=[{"role": "user", "content": prompt}], api_key=judge_key, temperature=0.0)

        try:
            response = await self.gateway.chat(request)
            winner, scores, reason = self._parse_judge(response.content, [r.model_id for r in successful])
        except AppError:
            # Judge failed: fall back to latency-ranked heuristic so compare still succeeds
            winner, scores, reason = self._heuristic_judge(successful)

        return winner, scores, reason

    def _judge_key(self) -> Optional[str]:
        # Server-side judge key from settings (env); falls back to None so the
        # gateway can use provider-stored credentials.
        return settings.judge_api_key or None

    def _parse_judge(self, text: str, model_ids) -> tuple[Optional[str], dict, str]:
        import re, json
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            data = json.loads(match.group(0))
            scores = {m: float(data.get("scores", {}).get(m, 0.0)) for m in model_ids}
            winner = data.get("winner")
            if winner not in scores and winner:
                winner = model_ids[0] if model_ids else None
            return winner, scores, data.get("reason", "No reason provided")
        except Exception:
            return self._heuristic_judge_from_scores(None, model_ids)

    def _heuristic_judge(self, successful) -> tuple[Optional[str], dict, str]:
        scores = {}
        for r in successful:
            latency_penalty = min(1.0, r.latency_ms / 10000)
            scores[r.model_id] = round(max(0.0, 8.0 - latency_penalty * 2 + r.output_tokens / 4000), 1)
        return self._heuristic_judge_from_scores(scores, [r.model_id for r in successful])

    def _heuristic_judge_from_scores(self, scores, model_ids) -> tuple[Optional[str], dict, str]:
        if not scores:
            scores = {m: 0.0 for m in model_ids}
        winner = max(scores.items(), key=lambda x: x[1])
        if winner[1] == 0:
            return model_ids[0] if model_ids else None, scores, "Judge could not be parsed; ranked by latency."
        return winner[0], scores, "Judge could not be parsed; ranked by latency and output size."

    def _run_to_dict(self, r: ModelRunResult) -> dict:
        return {
            "model_id": r.model_id,
            "provider_id": r.provider_id,
            "content": r.content,
            "status": r.status,
            "latency_ms": r.latency_ms,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "error_code": r.error_code,
            "error_message": r.error_message,
        }