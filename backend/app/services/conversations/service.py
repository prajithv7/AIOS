from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import Conversation, Message
from app.core.errors import AppError


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, user_id: str) -> list[dict]:
        convs = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.updated_at.desc())
        )
        result = []
        for c in convs.scalars().all():
            result.append({
                "id": c.id,
                "title": c.title or "New conversation",
                "project_id": c.project_id,
                "message_count": len(c.messages),
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            })
        return result

    async def create(self, user_id: str, title: str = None, project_id: str = None) -> Conversation:
        conv = Conversation(user_id=user_id, title=title, project_id=project_id)
        self.db.add(conv)
        await self.db.flush()
        await self.db.refresh(conv)
        await self.db.commit()
        return conv

    async def get(self, user_id: str, conversation_id: str) -> Conversation:
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        conv = (await self.db.execute(stmt)).scalar_one_or_none()
        if not conv or conv.user_id != user_id:
            raise AppError("FORBIDDEN", "Conversation not found or not owned", 404)
        return conv

    async def require(self, user_id: str, conversation_id: str) -> Conversation:
        return await self.get(user_id, conversation_id)

    async def list_messages(self, user_id: str, conversation_id: str) -> list[dict]:
        conv = await self.get(user_id, conversation_id)
        return [
            {
                "id": m.id,
                "conversation_id": m.conversation_id,
                "role": m.role,
                "content": m.content,
                "provider_id": m.provider_id,
                "model_id": m.model_id,
                "metadata": m.metadata_json,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in conv.messages
        ]

    async def get_history(self, user_id: str, conversation_id: str, limit: int = 20) -> list[dict]:
        conv = await self.get(user_id, conversation_id)
        msgs = conv.messages[-limit:] if limit else conv.messages
        return [{"role": m.role, "content": m.content} for m in msgs]

    def _build_context_messages(self, history: list[dict], content: str, max_context: int = 4000) -> list[dict]:
        trimmed = history[-(max_context // 4):]
        return [{"role": m["role"], "content": m["content"]} for m in trimmed] + [{"role": "user", "content": content}]

    async def add_user_message(self, conversation_id: str, content: str) -> Message:
        msg = Message(conversation_id=conversation_id, role="user", content=content)
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def add_assistant_message(self, conversation_id: str, content: str, provider_id: str = None, model_id: str = None) -> Message:
        msg = Message(
            conversation_id=conversation_id, role="assistant", content=content,
            provider_id=provider_id, model_id=model_id,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg