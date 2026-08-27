import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")
    app_name: str = "AIOS"
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    debug: bool = Field(default=True, validation_alias="DEBUG")

    database_url: str = Field(default="sqlite+aiosqlite:///./aios.db", validation_alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    master_key: str = Field(default="", validation_alias="MASTER_KEY")
    jwt_secret: str = Field(default="change-me-in-production", validation_alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = Field(default=15, validation_alias="JWT_ACCESS_EXPIRE_MINUTES")
    jwt_refresh_expire_days: int = Field(default=7, validation_alias="JWT_REFRESH_EXPIRE_DAYS")

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"], validation_alias="CORS_ORIGINS")
    frontend_url: str = Field(default="http://localhost:3000", validation_alias="FRONTEND_URL")

    litellm_base_url: str = Field(default="", validation_alias="LITELLM_BASE_URL")
    litellm_master_key: str = Field(default="", validation_alias="LITELLM_MASTER_KEY")

    judge_model: str = Field(default="openai/gpt-4o-mini", validation_alias="JUDGE_MODEL")
    judge_api_key: str = Field(default="", validation_alias="JUDGE_API_KEY")

    # Spec §16: rate-limit AI endpoints; limit request/message sizes.
    rate_limit_enabled: bool = Field(default=True, validation_alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=30, validation_alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, validation_alias="RATE_LIMIT_WINDOW_SECONDS")
    max_message_chars: int = Field(default=32000, validation_alias="MAX_MESSAGE_CHARS")
    max_compare_chars: int = Field(default=64000, validation_alias="MAX_COMPARE_CHARS")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()