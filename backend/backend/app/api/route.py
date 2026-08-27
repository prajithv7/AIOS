from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.client import get_db
from app.api.deps import get_current_user_id
from app.services.orchestration.service import OrchestrationService


router = APIRouter(prefix="/api/route", tags=["route"])


class RecommendRequest(BaseModel):
    content: str
    conversationId: str | None = None


@router.post("/recommend")
async def recommend(data: RecommendRequest, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = OrchestrationService(db)
    return await service.suggest_model(user_id, data.content, data.conversationId)