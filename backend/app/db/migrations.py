from sqlalchemy import text
from app.db.client import engine, init_db
from app.db.schema import Base, Provider, Model
from app.core.security import get_encryption
from app.core.config import settings
import json


DEFAULT_PROVIDERS = [
    {
        "id": "openai",
        "name": "OpenAI",
        "display_name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "auth_type": "bearer",
    },
    {
        "id": "anthropic",
        "name": "Anthropic",
        "display_name": "Anthropic",
        "base_url": "https://api.anthropic.com/v1",
        "auth_type": "bearer",
    },
    {
        "id": "gemini",
        "name": "Google Gemini",
        "display_name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "auth_type": "bearer",
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "display_name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "auth_type": "bearer",
    },
    {
        "id": "nvidia_nim",
        "name": "NVIDIA NIM",
        "display_name": "NVIDIA NIM",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "auth_type": "bearer",
    },
    {
        "id": "ollama",
        "name": "Ollama",
        "display_name": "Ollama (Local)",
        "base_url": "http://localhost:11434/v1",
        "auth_type": "none",
    },
]

DEFAULT_MODELS = [
    {"provider_id": "openai", "model_key": "gpt-4o", "display_name": "GPT-4o", "capabilities": {"coding": True, "reasoning": True, "vision": True, "long_context": True, "tool_use": True}, "context_window": 128000, "supports_streaming": True, "supports_tools": True, "supports_vision": True},
    {"provider_id": "openai", "model_key": "gpt-4o-mini", "display_name": "GPT-4o Mini", "capabilities": {"coding": True, "reasoning": True, "vision": True, "long_context": True, "tool_use": True}, "context_window": 128000, "supports_streaming": True, "supports_tools": True, "supports_vision": True},
    {"provider_id": "openai", "model_key": "o1-preview", "display_name": "o1 Preview", "capabilities": {"coding": True, "reasoning": True, "vision": False, "long_context": True, "tool_use": False}, "context_window": 128000, "supports_streaming": True, "supports_tools": False, "supports_vision": False},
    {"provider_id": "anthropic", "model_key": "claude-3-5-sonnet-20241022", "display_name": "Claude 3.5 Sonnet", "capabilities": {"coding": True, "reasoning": True, "vision": True, "long_context": True, "tool_use": True}, "context_window": 200000, "supports_streaming": True, "supports_tools": True, "supports_vision": True},
    {"provider_id": "anthropic", "model_key": "claude-3-5-haiku-20241022", "display_name": "Claude 3.5 Haiku", "capabilities": {"coding": True, "reasoning": True, "vision": True, "long_context": True, "tool_use": True}, "context_window": 200000, "supports_streaming": True, "supports_tools": True, "supports_vision": True},
    {"provider_id": "gemini", "model_key": "gemini-1.5-pro", "display_name": "Gemini 1.5 Pro", "capabilities": {"coding": True, "reasoning": True, "vision": True, "long_context": True, "tool_use": True}, "context_window": 2000000, "supports_streaming": True, "supports_tools": True, "supports_vision": True},
    {"provider_id": "gemini", "model_key": "gemini-1.5-flash", "display_name": "Gemini 1.5 Flash", "capabilities": {"coding": True, "reasoning": True, "vision": True, "long_context": True, "tool_use": True}, "context_window": 1000000, "supports_streaming": True, "supports_tools": True, "supports_vision": True},
    {"provider_id": "deepseek", "model_key": "deepseek-chat", "display_name": "DeepSeek V3", "capabilities": {"coding": True, "reasoning": True, "vision": False, "long_context": True, "tool_use": True}, "context_window": 128000, "supports_streaming": True, "supports_tools": True, "supports_vision": False},
    {"provider_id": "deepseek", "model_key": "deepseek-reasoner", "display_name": "DeepSeek R1", "capabilities": {"coding": True, "reasoning": True, "vision": False, "long_context": True, "tool_use": False}, "context_window": 128000, "supports_streaming": True, "supports_tools": False, "supports_vision": False},
    {"provider_id": "nvidia_nim", "model_key": "meta/llama-3.1-405b-instruct", "display_name": "Llama 3.1 405B", "capabilities": {"coding": True, "reasoning": True, "vision": False, "long_context": True, "tool_use": True}, "context_window": 128000, "supports_streaming": True, "supports_tools": True, "supports_vision": False},
    {"provider_id": "ollama", "model_key": "llama3.1:8b", "display_name": "Llama 3.1 8B (Local)", "capabilities": {"coding": True, "reasoning": False, "vision": False, "long_context": True, "tool_use": False}, "context_window": 128000, "supports_streaming": True, "supports_tools": False, "supports_vision": False},
    {"provider_id": "ollama", "model_key": "codellama:13b", "display_name": "CodeLlama 13B (Local)", "capabilities": {"coding": True, "reasoning": False, "vision": False, "long_context": False, "tool_use": False}, "context_window": 16384, "supports_streaming": True, "supports_tools": False, "supports_vision": False},
]


async def seed_default_data():
    from app.db.client import async_session_maker
    from sqlalchemy import select
    async with async_session_maker() as session:
        existing = await session.execute(select(Provider).limit(1))
        if existing.scalar_one_or_none():
            return

        for p in DEFAULT_PROVIDERS:
            session.add(Provider(**p))
        await session.flush()

        for m in DEFAULT_MODELS:
            session.add(Model(id=f"{m['provider_id']}/{m['model_key']}", **m))
        await session.commit()


async def run_migrations():
    await init_db()
    await seed_default_data()


async def create_tables():
    await init_db()