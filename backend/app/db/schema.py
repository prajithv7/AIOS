from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Index,
    Boolean,
    JSON,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
import uuid
import enum


Base = declarative_base()


def gen_id() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"
    id = Column(String(32), primary_key=True, default=gen_id)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    credentials = relationship("ApiCredential", back_populates="user", cascade="all, delete-orphan")
    user_providers = relationship("UserProvider", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"
    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash = Column(String(255), nullable=False)
    user_agent = Column(String(500))
    ip = Column(String(45))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="sessions")


class Provider(Base):
    __tablename__ = "providers"
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    base_url = Column(String(500))
    auth_type = Column(String(50), default="bearer")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    models = relationship("Model", back_populates="provider", cascade="all, delete-orphan")
    user_providers = relationship("UserProvider", back_populates="provider", cascade="all, delete-orphan")
    credentials = relationship("ApiCredential", back_populates="provider", cascade="all, delete-orphan")


class Model(Base):
    __tablename__ = "models"
    id = Column(String(100), primary_key=True)
    provider_id = Column(String(50), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True)
    model_key = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    capabilities = Column(JSON, default=dict)
    context_window = Column(Integer, default=4096)
    supports_streaming = Column(Boolean, default=True)
    supports_tools = Column(Boolean, default=False)
    supports_vision = Column(Boolean, default=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    provider = relationship("Provider", back_populates="models")
    __table_args__ = (UniqueConstraint("provider_id", "model_key", name="uq_provider_model"),)


class UserProvider(Base):
    __tablename__ = "user_providers"
    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(String(50), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="user_providers")
    provider = relationship("Provider", back_populates="user_providers")
    __table_args__ = (UniqueConstraint("user_id", "provider_id", name="uq_user_provider"),)


class ApiCredential(Base):
    __tablename__ = "api_credentials"
    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(String(50), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True)
    encrypted_key = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="credentials")
    provider = relationship("Provider", back_populates="credentials")
    __table_args__ = (UniqueConstraint("user_id", "provider_id", name="uq_user_credential"),)


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(32), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(200))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="conversations")
    project = relationship("Project", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    model_runs = relationship("ModelRun", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    id = Column(String(32), primary_key=True, default=gen_id)
    conversation_id = Column(String(32), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    provider_id = Column(String(50), ForeignKey("providers.id", ondelete="SET NULL"), nullable=True, index=True)
    model_id = Column(String(100), ForeignKey("models.id", ondelete="SET NULL"), nullable=True, index=True)
    metadata_json = Column("metadata_json", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")


class Project(Base):
    __tablename__ = "projects"
    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="projects")
    conversations = relationship("Conversation", back_populates="project")
    memory = relationship("ProjectMemory", back_populates="project", cascade="all, delete-orphan")


class MemoryType(str, enum.Enum):
    INSTRUCTIONS = "instructions"
    DECISIONS = "decisions"
    TECH_STACK = "tech_stack"
    PREFERENCES = "preferences"
    FILES = "files"
    NOTES = "notes"


class ProjectMemory(Base):
    __tablename__ = "project_memory"
    id = Column(String(32), primary_key=True, default=gen_id)
    project_id = Column(String(32), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(SQLEnum(MemoryType), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column("metadata_json", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="memory")
    __table_args__ = (Index("ix_project_memory_project_type", "project_id", "type"),)


class ModelRun(Base):
    __tablename__ = "model_runs"
    id = Column(String(32), primary_key=True, default=gen_id)
    conversation_id = Column(String(32), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(32), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True)
    provider_id = Column(String(50), ForeignKey("providers.id", ondelete="SET NULL"), nullable=True, index=True)
    model_id = Column(String(100), ForeignKey("models.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(20), default="pending")
    latency_ms = Column(Integer)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    error_code = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="model_runs")
    __table_args__ = (Index("ix_model_runs_conv_created", "conversation_id", "created_at"),)


class Comparison(Base):
    __tablename__ = "comparisons"
    id = Column(String(32), primary_key=True, default=gen_id)
    conversation_id = Column(String(32), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    task_message_id = Column(String(32), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True)
    winner_model_id = Column(String(100), ForeignKey("models.id", ondelete="SET NULL"), nullable=True)
    result = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("ix_comparisons_conv_created", "conversation_id", "created_at"),)


class FallbackEvent(Base):
    __tablename__ = "fallback_events"
    id = Column(String(32), primary_key=True, default=gen_id)
    conversation_id = Column(String(32), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    original_provider_id = Column(String(50), ForeignKey("providers.id", ondelete="SET NULL"), nullable=True)
    original_model_id = Column(String(100), ForeignKey("models.id", ondelete="SET NULL"), nullable=True)
    fallback_provider_id = Column(String(50), ForeignKey("providers.id", ondelete="SET NULL"), nullable=True)
    fallback_model_id = Column(String(100), ForeignKey("models.id", ondelete="SET NULL"), nullable=True)
    reason = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UsageRecord(Base):
    __tablename__ = "usage_records"
    id = Column(String(32), primary_key=True, default=gen_id)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(32), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    provider_id = Column(String(50), ForeignKey("providers.id", ondelete="SET NULL"), nullable=True)
    model_id = Column(String(100), ForeignKey("models.id", ondelete="SET NULL"), nullable=True)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("ix_usage_user_created", "user_id", "created_at"),)