from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.client import get_db
from app.api.deps import get_current_user_id
from app.services.routing.router import ModelService


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("")
async def list_providers(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = ModelService(db)
    return await service.list_providers(user_id)