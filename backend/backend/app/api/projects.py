from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.client import get_db
from app.api.deps import get_current_user_id
from app.services.memory.service import MemoryService
from app.services.conversations.service import ConversationService
from app.services.summary.service import SummaryService


router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class MemoryCreate(BaseModel):
    type: str
    content: str
    metadata: dict | None = None


class MemoryUpdate(BaseModel):
    content: str | None = None
    metadata: dict | None = None


@router.get("")
async def list_projects(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = MemoryService(db)
    return await service.list_projects(user_id)


@router.post("")
async def create_project(data: ProjectCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = MemoryService(db)
    p = await service.create_project(user_id, data.name, data.description)
    return {"id": p.id, "name": p.name, "description": p.description}


@router.get("/{project_id}")
async def get_project(project_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = MemoryService(db)
    p = await service.require_project(user_id, project_id)
    return {"id": p.id, "name": p.name, "description": p.description}


@router.get("/{project_id}/summary")
async def project_summary(project_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = SummaryService(db)
    return await service.project_summary(user_id, project_id)


@router.get("/{project_id}/conversations")
async def get_project_conversations(project_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    conv_service = ConversationService(db)
    all_convs = await conv_service.list(user_id)
    return [c for c in all_convs if c["project_id"] == project_id]


@router.get("/{project_id}/memory")
async def list_memory(project_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = MemoryService(db)
    return await service.list_memory(user_id, project_id)


@router.post("/{project_id}/memory")
async def create_memory(project_id: str, data: MemoryCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = MemoryService(db)
    return await service.create_memory(user_id, project_id, data.type, data.content, data.metadata)


@router.put("/{project_id}/memory/{memory_id}")
async def update_memory(project_id: str, memory_id: str, data: MemoryUpdate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = MemoryService(db)
    return await service.update_memory(user_id, project_id, memory_id, data.content, data.metadata)


@router.delete("/{project_id}/memory/{memory_id}")
async def delete_memory(project_id: str, memory_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = MemoryService(db)
    await service.delete_memory(user_id, project_id, memory_id)
    return {"ok": True}