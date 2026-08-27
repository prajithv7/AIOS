from dataclasses import dataclass
from typing import AsyncIterable, Optional, Any
import time

from app.core.errors import AppError


@dataclass
class ChatRequest:
    model_id: str
    messages: list[dict]
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None


@dataclass
class ChatResponse:
    content: str
    model_id: str
    provider_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    raw: dict = None


@dataclass
class ChatChunk:
    token: str
    model_id: str
    provider_id: str
    type: str = "token"


class LLMGateway:
    def __init__(self):
        self._litellm = None

    def litellm(self):
        if self._litellm is not None:
            return self._litellm
        try:
            import litellm
            self._litellm = litellm
        except ImportError as e:
            raise AppError("AI_REQUEST_FAILED", "LiteLLM is not installed", 500)
        return self._litellm

    def _model_info(self, model_id: str) -> tuple[str, str]:
        if "/" in model_id:
            provider_id, model_key = model_id.split("/", 1)
            return provider_id, model_key
        return "unknown", model_id

    def _normalize_error(self, exc: Exception) -> AppError:
        msg = str(exc).lower()
        if "unauthorized" in msg or "401" in msg or "api key" in msg or "auth" in msg:
            return AppError("PROVIDER_UNAUTHORIZED", "Provider API key invalid or missing", 401)
        if "rate" in msg or "429" in msg or "quota" in msg:
            return AppError("RATE_LIMITED", "Rate limit exceeded", 429)
        if "context" in msg or "length" in msg or "token" in msg:
            return AppError("CONTEXT_TOO_LARGE", "Conversation context exceeds model limit", 413)
        if "not found" in msg or "model" in msg or "404" in msg:
            return AppError("MODEL_NOT_FOUND", "Model not found", 404)
        if "timeout" in msg or "unavailable" in msg or "connection" in msg or "overloaded" in msg or "500" in msg or "502" in msg or "503" in msg:
            return AppError("PROVIDER_UNAVAILABLE", "The selected AI provider is temporarily unavailable", 503)
        return AppError("AI_REQUEST_FAILED", "AI request failed", 502)

    async def chat(self, request: ChatRequest) -> ChatResponse:
        litellm = self.litellm()
        provider_id, model_key = self._model_info(request.model_id)

        kwargs: dict[str, Any] = {
            "model": request.model_id,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False,
        }
        if request.api_key:
            kwargs["api_key"] = request.api_key

        start = time.perf_counter()
        try:
            response = await litellm.acompletion(**kwargs)
        except Exception as e:
            raise self._normalize_error(e)
        latency_ms = int((time.perf_counter() - start) * 1000)

        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

        return ChatResponse(
            content=content,
            model_id=request.model_id,
            provider_id=provider_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            raw=response,
        )

    async def stream(self, request: ChatRequest) -> AsyncIterable[ChatChunk]:
        litellm = self.litellm()
        provider_id, model_key = self._model_info(request.model_id)

        kwargs: dict[str, Any] = {
            "model": request.model_id,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": True,
        }
        if request.api_key:
            kwargs["api_key"] = request.api_key

        try:
            stream = await litellm.acompletion(**kwargs)
            async for chunk in stream:
                delta = chunk.choices[0].delta
                token = getattr(delta, "content", None)
                if token:
                    yield ChatChunk(token=token, model_id=request.model_id, provider_id=provider_id)
        except Exception as e:
            raise self._normalize_error(e)

    async def get_models(self, provider_id: str, api_key: Optional[str] = None) -> list[dict]:
        litellm = self.litellm()
        try:
            kwargs = {"model": f"{provider_id}/*"}
            if api_key:
                kwargs["api_key"] = api_key
            models = await litellm.alist_models(**kwargs)
            return [{"provider_id": provider_id, "model_key": m.id if hasattr(m, "id") else m} for m in models]
        except Exception:
            return []

    async def health_check(self, provider_id: str, api_key: Optional[str] = None) -> bool:
        litellm = self.litellm()
        try:
            await litellm.amodel_list({"model": f"{provider_id}/*"}) if api_key else None
            return True
        except Exception:
            return False