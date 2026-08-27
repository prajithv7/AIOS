from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.client import get_db
from app.api.deps import get_current_user


router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "name": user.name}


@router.get("/{user_id}")
async def user_detail(user_id: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.id != user_id:
        from app.core.errors import AppError
        raise AppError("FORBIDDEN", "Cannot view another user", 403)
    return {"id": user.id, "email": user.email, "name": user.name}