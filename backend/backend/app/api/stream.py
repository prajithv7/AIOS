from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

from app.db.client import get_db
from app.api.deps import get_current_user_id
from app.middleware.rate_limit import ai_rate_limit, validate_content_size
from app.core.config import settings
from app.services.orchestration.service import OrchestrationService
from app.core.errors import AppError


router = APIRouter(prefix="/chat", tags=["stream"])


class StreamRequest(BaseModel):
    conversationId: str
    content: str
    modelId: str


async def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/stream")
async def chat_stream(data: StreamRequest, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db), _: None = Depends(ai_rate_limit)):
    validate_content_size(data.content, settings.max_message_chars)
    service = OrchestrationService(db)

    async def gen():
        try:
            iterator = await service.stream(user_id, data.conversationId, data.content, data.modelId)
            async for chunk in iterator:
                if chunk.type == "done":
                    yield await sse_event("done", {"message_id": chunk.model_id})
                    return
                yield await sse_event("token", {"token": chunk.token, "model_id": chunk.model_id, "provider_id": chunk.provider_id})
        except AppError as e:
            yield await sse_event("error", {"code": e.code, "message": e.message})
        except Exception:
            yield await sse_event("error", {"code": "AI_REQUEST_FAILED", "message": "AI request failed"})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )