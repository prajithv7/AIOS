from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.client import get_db
from app.api.deps import get_current_user_id
from app.middleware.rate_limit import ai_rate_limit, validate_content_size
from app.core.config import settings
from app.services.comparison.service import ComparisonService
from app.services.conversations.service import ConversationService
from app.db.schema import Comparison


router = APIRouter(prefix="/api/compare", tags=["compare"])


class CompareRequest(BaseModel):
    conversationId: str | None = None
    content: str
    modelIds: list[str]


class CompareResponse(BaseModel):
    runId: str
    task: str
    runs: list[dict]
    winner: str | None
    scores: dict
    reason: str
    criteria: list[str]


@router.post("", response_model=CompareResponse)
async def compare(data: CompareRequest, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db), _: None = Depends(ai_rate_limit)):
    validate_content_size(data.content, settings.max_compare_chars, label="Compare content")
    service = ComparisonService(db)
    context = []
    if data.conversationId:
        conv_service = ConversationService(db)
        history = await conv_service.get_history(user_id, data.conversationId, limit=6)
        context = history

    result = await service.run(user_id, data.content, data.modelIds, context)

    comparison = Comparison(
        conversation_id=data.conversationId,
        task_message_id=None,
        winner_model_id=result["winner"],
        result=result,
    )
    db.add(comparison)
    await db.commit()
    await db.refresh(comparison)

    result["runId"] = comparison.id
    return result


@router.get("/{run_id}")
async def get_compare(run_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    comparison = await db.get(Comparison, run_id)
    if not comparison:
        from app.core.errors import AppError
        raise AppError("INVALID_REQUEST", "Comparison run not found", 404)
    result = comparison.result or {}
    result["runId"] = comparison.id
    return result