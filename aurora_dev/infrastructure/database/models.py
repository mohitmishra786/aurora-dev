"""
SQLAlchemy database models for AURORA-DEV.

This module defines the base model class and core database entities
for projects, tasks, and agent sessions.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TaskStatus(PyEnum):
    """Status enumeration for tasks."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_DEPENDENCY = "waiting_dependency"


class AgentSessionStatus(PyEnum):
    """Status enumeration for agent sessions."""

    IDLE = "idle"
    WORKING = "working"
    PAUSED = "paused"
    TERMINATED = "terminated"
    ERROR = "error"


class Project(Base, TimestampMixin):
    """Project entity representing a software development project."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    repository_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON config

    # Relationships
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    agent_sessions: Mapped[list["AgentSession"]] = relationship(
        "AgentSession",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"


class Task(Base, TimestampMixin):
    """Task entity representing a unit of work."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    complexity_score: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    estimated_duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    actual_duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON output

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    parent_task: Mapped[Optional["Task"]] = relationship(
        "Task",
        remote_side="Task.id",
        backref="subtasks",
    )
    assigned_agent: Mapped[Optional["AgentSession"]] = relationship(
        "AgentSession",
        back_populates="assigned_tasks",
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name='{self.name}', status={self.status})>"


class AgentSession(Base, TimestampMixin):
    """Agent session entity representing an active agent instance."""

    __tablename__ = "agent_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    agent_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # maestro, backend, frontend, etc.
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[AgentSessionStatus] = mapped_column(
        Enum(AgentSessionStatus),
        default=AgentSessionStatus.IDLE,
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_api_cost: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # in cents
    current_context: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON context
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="agent_sessions"
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="assigned_agent",
    )

    def __repr__(self) -> str:
        return f"<AgentSession(id={self.id}, agent_type='{self.agent_type}', status={self.status})>"


class ArchitectureDecision(Base, TimestampMixin):
    """Architecture Decision Record (ADR) entity."""

    __tablename__ = "architecture_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    alternatives_considered: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON
    consequences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    status: Mapped[str] = mapped_column(
        String(50), default="proposed", nullable=False
    )  # proposed, accepted, deprecated, superseded
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    def __repr__(self) -> str:
        return f"<ArchitectureDecision(id={self.id}, title='{self.title}')>"


class Reflection(Base, TimestampMixin):
    """Reflection/learning entity from agent execution."""

    __tablename__ = "reflections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    self_critique: Mapped[str] = mapped_column(Text, nullable=False)
    improved_approach: Mapped[str] = mapped_column(Text, nullable=False)
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    success: Mapped[bool] = mapped_column(default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<Reflection(id={self.id}, attempt={self.attempt_number}, success={self.success})>"
