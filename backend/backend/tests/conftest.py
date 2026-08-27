import os

os.environ.setdefault("MASTER_KEY", "test-master-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000"]')
