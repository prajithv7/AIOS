from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.client import get_db
from app.api.deps import get_current_user
from app.core.errors import AppError
from app.core.security import verify_password, hash_password


router = APIRouter(prefix="/api/users", tags=["users"])


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    current_password: str | None = None
    new_password: str | None = Field(default=None, min_length=8)


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "name": user.name}


@router.put("/me")
async def update_me(data: UserUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.db.schema import User as UserModel

    if data.name is not None:
        user.name = data.name

    if data.new_password is not None:
        if not data.current_password:
            raise AppError("INVALID_REQUEST", "Current password required to set new password", 422)
        if not verify_password(data.current_password, user.password_hash):
            raise AppError("INVALID_REQUEST", "Current password is incorrect", 401)
        user.password_hash = hash_password(data.new_password)

    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "email": user.email, "name": user.name}


@router.get("/{user_id}")
async def user_detail(user_id: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.id != user_id:
        raise AppError("FORBIDDEN", "Cannot view another user", 403)
    return {"id": user.id, "email": user.email, "name": user.name}