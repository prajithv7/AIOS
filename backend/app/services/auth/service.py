from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import User, Session as SessionModel
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.errors import AppError
import secrets


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def signup(self, email: str, name: str, password: str) -> dict:
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise AppError("INVALID_REQUEST", "Email already registered", 409)

        user = User(email=email, name=name, password_hash=hash_password(password))
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        access_token = create_access_token({"sub": user.id, "email": user.email})
        refresh_token = create_refresh_token({"sub": user.id})

        session = SessionModel(
            user_id=user.id,
            refresh_token_hash=hash_password(refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        self.db.add(session)
        await self.db.commit()

        return {
            "user": {"id": user.id, "email": user.email, "name": user.name},
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def login(self, email: str, password: str) -> dict:
        user = await self.db.execute(select(User).where(User.email == email))
        user = user.scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            raise AppError("AUTH_REQUIRED", "Invalid credentials", 401)

        access_token = create_access_token({"sub": user.id, "email": user.email})
        refresh_token = create_refresh_token({"sub": user.id})

        session = SessionModel(
            user_id=user.id,
            refresh_token_hash=hash_password(refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        self.db.add(session)
        await self.db.commit()

        return {
            "user": {"id": user.id, "email": user.email, "name": user.name},
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def refresh(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise AppError("AUTH_REQUIRED", "Invalid token type", 401)
            user_id = payload["sub"]
        except ValueError:
            raise AppError("AUTH_REQUIRED", "Invalid refresh token", 401)

        sessions = await self.db.execute(
            select(SessionModel).where(SessionModel.user_id == user_id)
        )
        session = next(
            (s for s in sessions.scalars().all() if verify_password(refresh_token, s.refresh_token_hash)),
            None,
        )
        if not session:
            raise AppError("AUTH_REQUIRED", "Session not found or revoked", 401)
        expires_at = session.expires_at
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at is None or expires_at < datetime.now(timezone.utc):
            raise AppError("AUTH_REQUIRED", "Refresh token expired", 401)

        user = await self.db.get(User, user_id)
        if not user:
            raise AppError("AUTH_REQUIRED", "User not found", 401)

        new_access = create_access_token({"sub": user.id, "email": user.email})
        new_refresh = create_refresh_token({"sub": user.id})

        session.refresh_token_hash = hash_password(new_refresh)
        session.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await self.db.commit()

        return {"access_token": new_access, "refresh_token": new_refresh}

    async def logout(self, refresh_token: str) -> bool:
        try:
            payload = decode_token(refresh_token)
            user_id = payload["sub"]
        except ValueError:
            return True

        await self.db.execute(delete(SessionModel).where(SessionModel.user_id == user_id))
        await self.db.commit()
        return True

    async def get_current_user(self, access_token: str) -> User:
        try:
            payload = decode_token(access_token)
            if payload.get("type") != "access":
                raise AppError("AUTH_REQUIRED", "Invalid token type", 401)
            user_id = payload["sub"]
        except ValueError:
            raise AppError("AUTH_REQUIRED", "Invalid access token", 401)

        user = await self.db.get(User, user_id)
        if not user:
            raise AppError("AUTH_REQUIRED", "User not found", 401)
        return user