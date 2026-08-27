from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.client import get_db
from app.services.auth.service import AuthService
from app.core.config import settings


router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    user: dict
    access_token: str
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str


def set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )


def clear_refresh_cookie(response: Response):
    response.delete_cookie(key="refresh_token", path="/", httponly=True, secure=settings.app_env == "production")


@router.post("/signup", response_model=TokenResponse)
async def signup(data: SignupRequest, response: Response, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.signup(data.email, data.name, data.password)
    set_refresh_cookie(response, result["refresh_token"])
    return {"user": result["user"], "access_token": result["access_token"], "refresh_token": result["refresh_token"]}


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.login(data.email, data.password)
    set_refresh_cookie(response, result["refresh_token"])
    return {"user": result["user"], "access_token": result["access_token"], "refresh_token": result["refresh_token"]}


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    response: Response,
    refresh_token: str = Cookie(None),
    body: RefreshRequest = None,
    db: AsyncSession = Depends(get_db),
):
    token = refresh_token or (body.refresh_token if body else None)
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token required")
    service = AuthService(db)
    result = await service.refresh(token)
    set_refresh_cookie(response, result["refresh_token"])
    return result


@router.post("/logout")
async def logout(response: Response, refresh_token: str = Cookie(None), db: AsyncSession = Depends(get_db)):
    if refresh_token:
        service = AuthService(db)
        await service.logout(refresh_token)
    clear_refresh_cookie(response)
    return {"ok": True}