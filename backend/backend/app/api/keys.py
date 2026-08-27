from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.client import get_db
from app.services.credentials.service import CredentialsService
from app.api.deps import get_current_user_id


router = APIRouter(prefix="/api/keys", tags=["keys"])


class SetKeyRequest(BaseModel):
    provider_id: str
    api_key: str


class KeyStatusResponse(BaseModel):
    provider_id: str
    name: str
    display_name: str
    connected: bool
    active: bool
    masked_key: str | None = None


@router.post("")
async def set_key(data: SetKeyRequest, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = CredentialsService(db)
    return await service.set_key(user_id, data.provider_id, data.api_key)


@router.delete("/{provider_id}")
async def delete_key(provider_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = CredentialsService(db)
    await service.delete_key(user_id, provider_id)
    return {"ok": True}


@router.get("", response_model=list[KeyStatusResponse])
async def list_keys(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = CredentialsService(db)
    return await service.list_status(user_id)