from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.client import get_db
from app.api.deps import get_current_user_id
from app.middleware.rate_limit import ai_rate_limit, validate_content_size
from app.core.config import settings
from app.services.conversations.service import ConversationService


router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", max_length=200)
    project_id: str | None = None


class ConversationUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    project_id: str | None = None


class MessageCreate(BaseModel):
    content: str
    modelId: str | None = None
    allowFallback: bool = True


@router.get("")
async def list_conversations(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = ConversationService(db)
    return await service.list(user_id)


@router.post("")
async def create_conversation(data: ConversationCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = ConversationService(db)
    conv = await service.create(user_id, data.title, data.project_id)
    return {"id": conv.id, "title": conv.title, "project_id": conv.project_id}

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = ConversationService(db)
    conv = await service.get(user_id, conversation_id)
    return {"id": conv.id, "title": conv.title, "project_id": conv.project_id}


@router.patch("/{conversation_id}")
async def update_conversation(conversation_id: str, data: ConversationUpdate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = ConversationService(db)
    return await service.update(user_id, conversation_id, data.title, data.project_id)


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = ConversationService(db)
    await service.delete(user_id, conversation_id)
    return {"ok": True}

@router.get("/{conversation_id}/messages")
async def list_messages(conversation_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = ConversationService(db)
    return await service.list_messages(user_id, conversation_id)


@router.post("/{conversation_id}/messages")
async def send_message(conversation_id: str, data: MessageCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db), _: None = Depends(ai_rate_limit)):
    validate_content_size(data.content, settings.max_message_chars)
    from app.services.orchestration.service import OrchestrationService
    service = OrchestrationService(db)
    return await service.send_message(user_id, conversation_id, data.content, data.modelId, data.allowFallback)