from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.schema import (
    Project,
    ProjectMemory,
    Conversation,
    Message,
    ModelRun,
    Comparison,
    FallbackEvent,
)
from app.core.errors import AppError


class SummaryService:
    """Compiles a deterministic markdown report for a project (spec §1 goal)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def project_summary(self, user_id: str, project_id: str) -> dict:
        stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.memory),
                selectinload(Project.conversations).selectinload(Conversation.messages),
            )
        )
        project = (await self.db.execute(stmt)).scalar_one_or_none()
        if not project or project.user_id != user_id:
            raise AppError("FORBIDDEN", "Project not found or not owned", 404)

        conv_ids = [c.id for c in project.conversations]
        runs = {}
        comparisons = {}
        fallbacks = {}
        if conv_ids:
            runs = await self._index(self.db, ModelRun, "conversation_id", conv_ids)
            comparisons = await self._index(self.db, Comparison, "conversation_id", conv_ids)
            fallbacks = await self._index(self.db, FallbackEvent, "conversation_id", conv_ids)

        md = self._render(project, runs, comparisons, fallbacks)
        return {
            "project_id": project.id,
            "filename": f"{project.name or 'project'}-summary.md",
            "markdown": md,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _index(self, db, model, key_col, conv_ids) -> dict:
        rows = await db.execute(select(model).where(getattr(model, key_col).in_(conv_ids)))
        result = {}
        for r in rows.scalars().all():
            result.setdefault(getattr(r, key_col), []).append(r)
        return result

    def _render(self, project, runs, comparisons, fallbacks) -> str:
        lines = []
        lines.append(f"# Project Summary — {project.name or 'Untitled'}")
        lines.append("")
        lines.append(f"> Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        if project.description:
            lines.append("")
            lines.append(f"**Description:** {project.description}")
        lines.append("")

        # Memory
        if project.memory:
            lines.append("## Project memory")
            lines.append("")
            for e in project.memory:
                lines.append(f"- **{e.type.value if hasattr(e.type, 'value') else e.type}:** {e.content}")
            lines.append("")

        # Conversations
        lines.append(f"## Conversations ({len(project.conversations)})")
        lines.append("")
        for conv in project.conversations:
            lines.append(f"### {conv.title or 'New conversation'}")
            lines.append("")
            for m in conv.messages:
                author = "Assistant" if m.role == "assistant" else m.role.capitalize()
                model = f" _({m.model_id})_" if m.model_id else ""
                lines.append(f"> **{author}**{model}")
                lines.append(">")
                for chunk in m.content.splitlines():
                    lines.append(f"> {chunk}")
                lines.append("")

            conv_runs = runs.get(conv.id, [])
            if conv_runs:
                lines.append("")
                lines.append("**Model activity:**")
                for r in conv_runs:
                    status = r.status
                    extra = f" ({r.latency_ms}ms, {r.input_tokens}→{r.output_tokens} tok)" if r.status == "success" else f" ({r.error_code or status})"
                    lines.append(f"- `{r.model_id}` — {status}{extra}")
                lines.append("")

            conv_comps = comparisons.get(conv.id, [])
            for c in conv_comps:
                lines.append("")
                lines.append(f"**Comparison:** winner `{c.winner_model_id}`")
            lines.append("")

        # Fallback events
        total_fb = sum(len(v) for v in fallbacks.values())
        if total_fb:
            lines.append(f"## Fallback events ({total_fb})")
            lines.append("")
            for events in fallbacks.values():
                for e in events:
                    lines.append(
                        f"- `{e.original_model_id}` → `{e.fallback_model_id}` ({e.reason})"
                    )
            lines.append("")

        return "\n".join(lines)