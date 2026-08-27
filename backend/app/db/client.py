from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.core.config import settings
from app.db.schema import Base


def _resolve_engine_url(raw: str) -> str:
    """Translate the Turso ``libsql://`` URL to the async libSQL dialect.

    The ``sqlalchemy-libsql`` package only ships a *sync* DBAPI and its async
    dialect is broken for ``create_async_engine``, so we use a thin async
    adapter (``app.db.libsql_async``) that wraps the sync ``libsql_experimental``
    DBAPI.  No schema, model or service code is changed.
    """
    if raw.startswith("libsql://"):
        import app.db.libsql_async  # noqa: F401  (registers the "libsql.async" dialect)

        return "libsql+async://" + raw[len("libsql://"):]
    return raw


_engine_url = _resolve_engine_url(settings.database_url)
_is_libsql = _engine_url.startswith("libsql+async://")

engine = create_async_engine(
    _engine_url,
    echo=settings.debug,
    poolclass=NullPool if (_is_libsql or "sqlite" in settings.database_url) else None,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    await engine.dispose()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_session() as session:
        yield session