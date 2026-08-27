from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import ApiCredential, Provider, UserProvider
from app.core.security import get_encryption, mask_key
from app.core.errors import AppError


class CredentialsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.encryption = get_encryption()

    async def set_key(self, user_id: str, provider_id: str, api_key: str) -> dict:
        provider = await self.db.get(Provider, provider_id)
        if not provider:
            raise AppError("PROVIDER_NOT_FOUND", "Provider not found", 404)

        encrypted = self.encryption.encrypt(api_key)

        cred = await self.db.execute(
            select(ApiCredential).where(ApiCredential.user_id == user_id, ApiCredential.provider_id == provider_id)
        )
        cred = cred.scalar_one_or_none()
        if cred:
            cred.encrypted_key = encrypted
            cred.updated_at = datetime.utcnow()
        else:
            cred = ApiCredential(user_id=user_id, provider_id=provider_id, encrypted_key=encrypted)
            self.db.add(cred)

        up = await self.db.execute(
            select(UserProvider).where(UserProvider.user_id == user_id, UserProvider.provider_id == provider_id)
        )
        up = up.scalar_one_or_none()
        if not up:
            up = UserProvider(user_id=user_id, provider_id=provider_id, is_active=True)
            self.db.add(up)
        else:
            up.is_active = True

        await self.db.commit()
        return {"provider_id": provider_id, "status": "connected", "masked_key": mask_key(api_key)}

    async def delete_key(self, user_id: str, provider_id: str) -> bool:
        cred = await self.db.execute(
            select(ApiCredential).where(ApiCredential.user_id == user_id, ApiCredential.provider_id == provider_id)
        )
        cred = cred.scalar_one_or_none()
        if not cred:
            raise AppError("PROVIDER_UNAUTHORIZED", "No key configured for this provider", 401)
        await self.db.delete(cred)

        up = await self.db.execute(
            select(UserProvider).where(UserProvider.user_id == user_id, UserProvider.provider_id == provider_id)
        )
        up = up.scalar_one_or_none()
        if up:
            up.is_active = False

        await self.db.commit()
        return True

    async def get_key(self, user_id: str, provider_id: str) -> str:
        cred = await self.db.execute(
            select(ApiCredential).where(ApiCredential.user_id == user_id, ApiCredential.provider_id == provider_id)
        )
        cred = cred.scalar_one_or_none()
        if not cred:
            raise AppError("PROVIDER_UNAUTHORIZED", "No key configured for this provider", 401)
        return self.encryption.decrypt(cred.encrypted_key)

    async def list_status(self, user_id: str) -> list[dict]:
        providers = await self.db.execute(select(Provider).where(Provider.enabled == True))
        providers = providers.scalars().all()

        creds = await self.db.execute(select(ApiCredential).where(ApiCredential.user_id == user_id))
        creds = {c.provider_id: c for c in creds.scalars().all()}

        ups = await self.db.execute(select(UserProvider).where(UserProvider.user_id == user_id))
        ups = {u.provider_id: u.is_active for u in ups.scalars().all()}

        result = []
        for p in providers:
            cred = creds.get(p.id)
            result.append({
                "provider_id": p.id,
                "name": p.name,
                "display_name": p.display_name,
                "connected": p.id in creds,
                "active": ups.get(p.id, False),
                "masked_key": mask_key(self.encryption.decrypt(cred.encrypted_key)) if cred else None,
            })
        return result

    async def get_decrypted_keys(self, user_id: str) -> dict[str, str]:
        creds = await self.db.execute(select(ApiCredential).where(ApiCredential.user_id == user_id))
        return {c.provider_id: self.encryption.decrypt(c.encrypted_key) for c in creds.scalars().all()}