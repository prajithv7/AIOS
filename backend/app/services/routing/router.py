from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import Model, Provider, UserProvider, ApiCredential
from app.core.errors import AppError


class ModelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_models(self, user_id: str = None) -> list[dict]:
        models = await self.db.execute(select(Model).where(Model.status == "active"))
        models = models.scalars().all()

        authorized = set()
        if user_id:
            ups = await self.db.execute(select(UserProvider).where(UserProvider.user_id == user_id, UserProvider.is_active == True))
            authorized = {u.provider_id for u in ups.scalars().all()}

        result = []
        for m in models:
            provider_ok = (not user_id) or (m.provider_id in authorized)
            result.append({
                "model_id": m.id,
                "provider_id": m.provider_id,
                "display_name": m.display_name,
                "capabilities": m.capabilities,
                "context_window": m.context_window,
                "supports_streaming": m.supports_streaming,
                "supports_tools": m.supports_tools,
                "supports_vision": m.supports_vision,
                "status": m.status,
                "authorized": provider_ok,
            })
        return result

    async def get_model(self, model_id: str) -> Model:
        model = await self.db.get(Model, model_id)
        if not model:
            raise AppError("MODEL_NOT_FOUND", "Model not found", 404)
        return model

    async def list_providers(self, user_id: str = None) -> list[dict]:
        providers = await self.db.execute(select(Provider).where(Provider.enabled == True))
        providers = providers.scalars().all()

        creds = set()
        if user_id:
            c = await self.db.execute(select(ApiCredential).where(ApiCredential.user_id == user_id))
            creds = {x.provider_id for x in c.scalars().all()}

        return [
            {
                "provider_id": p.id,
                "name": p.name,
                "display_name": p.display_name,
                "auth_type": p.auth_type,
                "connected": user_id is None or p.id in creds,
            }
            for p in providers
        ]

    async def get_authorized_provider_ids(self, user_id: str) -> set[str]:
        creds = await self.db.execute(select(ApiCredential).where(ApiCredential.user_id == user_id))
        return {c.provider_id for c in creds.scalars().all()}


class ModelRegistry:
    """Model Registry + simple capability-based routing (backend $6, $11)."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.service = ModelService(db)

    async def recommend(self, user_id: str, content: str) -> dict:
        models = await self.service.list_models(user_id)
        authorized = [m for m in models if m["authorized"] and m["status"] == "active"]
        if not authorized:
            raise AppError("PROVIDER_UNAUTHORIZED", "No authorized AI providers. Please connect a provider key.", 401)

        task_type = self._classify(content)
        required = TASK_CAPABILITIES.get(task_type, {})

        ranked = []
        for m in authorized:
            caps = m["capabilities"]
            score = sum(1 for k, v in required.items() if caps.get(k) == v)
            ranking = score * 10 + (1 if caps.get("reasoning") else 0)
            ranked.append((ranking, m))

        ranked.sort(key=lambda x: x[0], reverse=True)
        best = ranked[0][1] if ranked else authorized[0]
        return {"task_type": task_type, "recommended_model_id": best["model_id"], "candidates": [m["model_id"] for _, m in ranked[:5]]}

    def _classify(self, content: str) -> str:
        text = content.lower()
        if any(k in text for k in ["code", "function", "python", "javascript", "debug", "refactor", "bug", "api", "sql", "react", "algorithm"]):
            return "coding"
        if any(k in text for k in ["reason", "logic", "solve", "analyze", "math", "prove", "derive"]):
            return "reasoning"
        if any(k in text for k in ["summarize", "long", "document", "read", "report", "paper", "context"]):
            return "long_document"
        if any(k in text for k in ["image", "photo", "picture", "screenshot", "vision", "see", "diagram"]):
            return "vision"
        return "general"


TASK_CAPABILITIES = {
    "coding": {"coding": True},
    "reasoning": {"reasoning": True},
    "long_document": {"long_context": True},
    "vision": {"vision": True},
    "general": {},
}