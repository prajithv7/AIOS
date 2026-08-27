from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.errors import (
    validation_exception_handler,
    http_exception_handler,
    app_error_handler,
    generic_exception_handler,
    AppError,
)
from app.db.client import close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.migrations import run_migrations
    await run_migrations()
    yield
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name}


from app.api import auth, keys, providers, models, conversations, messages, compare, route, projects, users, stream

app.include_router(auth.router)
app.include_router(keys.router)
app.include_router(providers.router)
app.include_router(models.router)
app.include_router(conversations.router)
app.include_router(messages.router)
app.include_router(compare.router)
app.include_router(route.router)
app.include_router(projects.router)
app.include_router(users.router)
app.include_router(stream.router)