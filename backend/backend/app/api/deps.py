from fastapi import Depends, HTTPException, Cookie, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.client import get_db
from app.services.auth.service import AuthService


def _extract_token(access_token: str, authorization: str) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    if access_token:
        return access_token
    return None


async def get_current_user_id(
    access_token: str = Cookie(None),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> str:
    token = _extract_token(access_token, authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    service = AuthService(db)
    user = await service.get_current_user(token)
    return user.id


async def get_current_user(
    access_token: str = Cookie(None),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    token = _extract_token(access_token, authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    service = AuthService(db)
    return await service.get_current_user(token)