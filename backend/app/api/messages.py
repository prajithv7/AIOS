from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.client import get_db
from app.api.deps import get_current_user_id
from app.middleware.rate_limit import ai_rate_limit, validate_content_size
from app.core.config import settings
from app.services.orchestration.service import OrchestrationService


router = APIRouter(prefix="/api/messages", tags=["messages"])


class SendMessageRequest(BaseModel):
    content: str
    modelId: str | None = None
    conversationId: str
    allowFallback: bool = True


@router.post("")
async def send_message(data: SendMessageRequest, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db), _: None = Depends(ai_rate_limit)):
    validate_content_size(data.content, settings.max_message_chars)
    service = OrchestrationService(db)
    return await service.send_message(
        user_id, data.conversationId, data.content, data.modelId, data.allowFallback
    )