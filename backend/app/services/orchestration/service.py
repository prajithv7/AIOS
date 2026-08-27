from typing import Optional

from app.db.schema import ModelRun, FallbackEvent as FallbackEventModel, Conversation
from app.providers.llm_gateway import LLMGateway, ChatRequest, ChatChunk
from app.services.credentials.service import CredentialsService
from app.services.conversations.service import ConversationService
from app.services.memory.service import MemoryService
from app.services.health.service import ProviderHealthService
from app.services.routing.router import ModelService, ModelRegistry
from app.services.context.budget import fit_messages_to_budget
from app.core.errors import AppError
from app.core.config import settings


class OrchestrationService:
    def __init__(self, db):
        self.db = db
        self.gateway = LLMGateway()
        self.credentials = CredentialsService(db)
        self.conversations = ConversationService(db)
        self.memory = MemoryService(db)
        self.health = ProviderHealthService()
        self.models = ModelService(db)
        self.registry = ModelRegistry(db)

    async def _build_context(self, user_id: str, conv: Conversation, content: str, limit: int = 20, context_window: Optional[int] = None) -> list[dict]:
        """Load conversation history plus relevant project memory (spec §4 step 2, §8).

        Project memory is injected as a leading system message, keeping it distinct
        from chat history so model switches never lose it while normal context is trimmed.
        When ``context_window`` is given, the result is token-budgeted for the
        target model (spec §7): system messages preserved, newest history kept.
        """
        history = await self.conversations.get_history(user_id, conv.id, limit=limit)
        context = self.conversations._build_context_messages(history, content)

        if conv.project_id:
            try:
                memory = await self.memory.get_relevant_memory(conv.project_id, limit=8)
                if memory:
                    memory_block = "\n".join(f"- {m}" for m in memory)
                    context.insert(0, {
                        "role": "system",
                        "content": f"Project context:\n{memory_block}",
                    })
            except AppError:
                pass

        if context_window:
            context = fit_messages_to_budget(context, context_window)
        return context

    async def suggest_model(self, user_id: str, content: str, conversation_id: Optional[str] = None) -> dict:
        return await self.registry.recommend(user_id, content)

    async def send_message(
        self,
        user_id: str,
        conversation_id: str,
        content: str,
        model_id: Optional[str] = None,
        allow_fallback: bool = True,
    ) -> dict:
        conv = await self.conversations.require(user_id, conversation_id)

        if not model_id:
            rec = await self.registry.recommend(user_id, content)
            model_id = rec["recommended_model_id"]

        model = await self.models.get_model(model_id)
        if model.provider_id not in await self.models.get_authorized_provider_ids(user_id):
            raise AppError("PROVIDER_UNAUTHORIZED", f"Provider {model.provider_id} is not authorized", 401)

        context_messages = await self._build_context(user_id, conv, content, context_window=model.context_window)

        user_message = await self.conversations.add_user_message(conversation_id, content)
        await self.db.flush()

        api_key = await self.credentials.get_key(user_id, model.provider_id)
        request = ChatRequest(model_id=model_id, messages=context_messages, api_key=api_key)

        original_model = model
        try:
            response = await self.gateway.chat(request)
            used_model = original_model
        except AppError as e:
            await self.health.record_failure(original_model.provider_id)
            if not allow_fallback:
                raise e
            used_model = await self._fallback(user_id, conv, original_model, content, api_key, e)
            # Fallback model may have a different context window: re-budget.
            fallback_messages = await self._build_context(
                user_id, conv, content, context_window=used_model.context_window
            )
            response = await self.gateway.chat(
                ChatRequest(model_id=used_model.id, messages=fallback_messages, api_key=await self._provider_key(user_id, used_model.provider_id))
            )

        await self.health.record_success(used_model.provider_id)

        assistant_msg = await self.conversations.add_assistant_message(
            conversation_id, response.content, provider_id=used_model.provider_id, model_id=used_model.id
        )

        run = ModelRun(
            conversation_id=conversation_id,
            message_id=assistant_msg.id,
            provider_id=used_model.provider_id,
            model_id=used_model.id,
            status="success",
            latency_ms=response.latency_ms,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )
        self.db.add(run)
        await self.db.commit()

        return {
            "message": {
                "id": assistant_msg.id,
                "role": "assistant",
                "content": response.content,
                "provider_id": used_model.provider_id,
                "model_id": used_model.id,
            },
            "model_id": used_model.id,
            "provider_id": used_model.provider_id,
            "latency_ms": response.latency_ms,
            "tokens": {"input": response.input_tokens, "output": response.output_tokens},
        }

    async def _fallback(self, user_id, conv, original_model, content, api_key, error: AppError):
        candidates = await self.models.list_models(user_id)
        candidates = [m for m in candidates if m["authorized"] and m["model_id"] != original_model.id]

        healthy = []
        for c in candidates:
            if await self.health.is_healthy(c["provider_id"]):
                healthy.append(c)

        for c in healthy:
            event = FallbackEventModel(
                conversation_id=conv.id,
                original_provider_id=original_model.provider_id,
                original_model_id=original_model.id,
                fallback_provider_id=c["provider_id"],
                fallback_model_id=c["model_id"],
                reason=error.code,
            )
            self.db.add(event)
            try:
                key = await self.credentials.get_key(user_id, c["provider_id"])
                request = ChatRequest(model_id=c["model_id"], messages=[{"role": "user", "content": content}], api_key=key)
                await self.gateway.chat(request)
                await self.db.flush()
                return await self.models.get_model(c["model_id"])
            except AppError:
                await self.health.record_failure(c["provider_id"])
                continue

        raise error

    async def _provider_key(self, user_id, provider_id) -> Optional[str]:
        try:
            return await self.credentials.get_key(user_id, provider_id)
        except AppError:
            return None

    async def stream(self, user_id, conversation_id, content, model_id) -> "async iterator":
        conv = await self.conversations.require(user_id, conversation_id)
        model = await self.models.get_model(model_id)

        context_messages = await self._build_context(user_id, conv, content, context_window=model.context_window)
        api_key = await self.credentials.get_key(user_id, model.provider_id)
        request = ChatRequest(model_id=model_id, messages=context_messages, api_key=api_key, temperature=0.7)

        async def gen():
            buffer = []
            try:
                async for chunk in self.gateway.stream(request):
                    buffer.append(chunk.token)
                    yield chunk
                full = "".join(buffer)
                await self.conversations.add_user_message(conversation_id, content)
                msg = await self.conversations.add_assistant_message(conversation_id, full, provider_id=model.provider_id, model_id=model.id)
                run = ModelRun(conversation_id=conversation_id, message_id=msg.id, provider_id=model.provider_id,
                               model_id=model.id, status="success")
                self.db.add(run)
                await self.db.commit()
                await self.health.record_success(model.provider_id)
                yield ChatChunk(token="", model_id=model.id, provider_id=model.provider_id, type="done")
            except AppError as e:
                # Persist failed run
                try:
                    await self.health.record_failure(model.provider_id)
                    await self.conversations.add_user_message(conversation_id, content)
                    run = ModelRun(conversation_id=conversation_id, provider_id=model.provider_id,
                                   model_id=model.id, status="failed", error_code=e.code)
                    self.db.add(run)
                    await self.db.commit()
                except Exception:
                    pass
                raise e

        return gen()