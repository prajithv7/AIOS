from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import Project, ProjectMemory, MemoryType
from app.core.errors import AppError


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_projects(self, user_id: str) -> list[dict]:
        projects = await self.db.execute(select(Project).where(Project.user_id == user_id).order_by(Project.updated_at.desc()))
        result = []
        for p in projects.scalars().all():
            result.append({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "conversation_count": len(p.conversations),
                "memory_count": len(p.memory),
                "last_active": p.updated_at.isoformat() if p.updated_at else None,
            })
        return result

    async def create_project(self, user_id: str, name: str, description: str = None) -> Project:
        project = Project(user_id=user_id, name=name, description=description)
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        await self.db.commit()
        return project

    async def get_project(self, user_id: str, project_id: str) -> Project:
        project = await self.db.get(Project, project_id)
        if not project or project.user_id != user_id:
            raise AppError("FORBIDDEN", "Project not found or not owned", 404)
        return project

    async def require_project(self, user_id: str, project_id: str) -> Project:
        return await self.get_project(user_id, project_id)

    async def list_memory(self, user_id: str, project_id: str) -> list[dict]:
        await self.require_project(user_id, project_id)
        entries = await self.db.execute(
            select(ProjectMemory).where(ProjectMemory.project_id == project_id).order_by(ProjectMemory.created_at)
        )
        return [
            {
                "id": e.id,
                "type": e.type.value if hasattr(e.type, "value") else str(e.type),
                "content": e.content,
                "metadata": e.metadata_json,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries.scalars().all()
        ]

    async def create_memory(self, user_id: str, project_id: str, type_: str, content: str, metadata: dict = None) -> dict:
        await self.require_project(user_id, project_id)
        try:
            mtype = MemoryType(type_)
        except ValueError:
            raise AppError("INVALID_REQUEST", f"Invalid memory type: {type_}", 422)
        entry = ProjectMemory(project_id=project_id, type=mtype, content=content, metadata_json=metadata or {})
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)
        return {"id": entry.id, "type": type_, "content": entry.content, "metadata": entry.metadata_json}

    async def update_memory(self, user_id: str, project_id: str, memory_id: str, content: str = None, metadata: dict = None) -> dict:
        await self.require_project(user_id, project_id)
        entry = await self.db.get(ProjectMemory, memory_id)
        if not entry or entry.project_id != project_id:
            raise AppError("FORBIDDEN", "Memory not found", 404)
        if content is not None:
            entry.content = content
        if metadata is not None:
            entry.metadata_json = metadata
        await self.db.commit()
        await self.db.refresh(entry)
        return {"id": entry.id, "type": entry.type.value if hasattr(entry.type, "value") else str(entry.type),
                "content": entry.content, "metadata": entry.metadata_json}

    async def delete_memory(self, user_id: str, project_id: str, memory_id: str) -> bool:
        await self.require_project(user_id, project_id)
        entry = await self.db.get(ProjectMemory, memory_id)
        if not entry or entry.project_id != project_id:
            raise AppError("FORBIDDEN", "Memory not found", 404)
        await self.db.delete(entry)
        await self.db.commit()
        return True

    async def get_relevant_memory(self, project_id: str, limit: int = 8) -> list[str]:
        entries = await self.db.execute(
            select(ProjectMemory).where(ProjectMemory.project_id == project_id).order_by(ProjectMemory.updated_at.desc()).limit(limit)
        )
        return [e.content for e in entries.scalars().all()]