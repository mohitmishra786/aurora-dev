"""
Task priority and status definitions for AURORA-DEV.

Provides enumerations and data classes for task management
including priority levels, status tracking, and task metadata.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class TaskPriority(Enum):
    """Task priority levels for queue ordering.
    
    Higher values indicate higher priority.
    """
    
    CRITICAL = 10
    HIGH = 7
    MEDIUM = 5
    LOW = 3
    BACKGROUND = 1


class TaskStatus(Enum):
    """Task execution status.
    
    Tracks the lifecycle of a task from creation to completion.
    """
    
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskType(Enum):
    """Types of tasks that can be executed.
    
    Maps to different agent operations and workflows.
    """
    
    AGENT_EXECUTION = "agent_execution"
    REFLEXION = "reflexion"
    AGGREGATION = "aggregation"
    WORKFLOW_STEP = "workflow_step"
    HEALTH_CHECK = "health_check"


@dataclass
class TaskMetadata:
    """Metadata for task tracking and monitoring.
    
    Attributes:
        task_id: Unique task identifier.
        task_type: Type of task being executed.
        priority: Task priority level.
        status: Current task status.
        created_at: Task creation timestamp.
        started_at: Optional task start timestamp.
        completed_at: Optional task completion timestamp.
        retry_count: Number of retry attempts.
        max_retries: Maximum allowed retries.
        timeout_seconds: Task timeout in seconds.
        project_id: Associated project identifier.
        agent_id: Optional assigned agent identifier.
        parent_task_id: Optional parent task for sub-tasks.
        tags: Optional tags for categorization.
        extra: Additional metadata.
    """
    
    task_id: str = field(default_factory=lambda: str(uuid4()))
    task_type: TaskType = TaskType.AGENT_EXECUTION
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
    project_id: Optional[str] = None
    agent_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state.
        
        Returns:
            True if task has completed (success, failed, cancelled, timeout).
        """
        return self.status in {
            TaskStatus.SUCCESS,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        }
    
    @property
    def can_retry(self) -> bool:
        """Check if task can be retried.
        
        Returns:
            True if retry count is below maximum.
        """
        return self.retry_count < self.max_retries
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration in seconds.
        
        Returns:
            Duration if task has started, None otherwise.
        """
        if self.started_at is None:
            return None
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary.
        
        Returns:
            Dictionary representation of metadata.
        """
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "project_id": self.project_id,
            "agent_id": self.agent_id,
            "parent_task_id": self.parent_task_id,
            "tags": self.tags,
            "extra": self.extra,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskMetadata":
        """Create metadata from dictionary.
        
        Args:
            data: Dictionary with metadata fields.
            
        Returns:
            TaskMetadata instance.
        """
        return cls(
            task_id=data.get("task_id", str(uuid4())),
            task_type=TaskType(data.get("task_type", "agent_execution")),
            priority=TaskPriority(data.get("priority", 5)),
            status=TaskStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 300),
            project_id=data.get("project_id"),
            agent_id=data.get("agent_id"),
            parent_task_id=data.get("parent_task_id"),
            tags=data.get("tags", []),
            extra=data.get("extra", {}),
        )


@dataclass
class TaskPayload:
    """Complete task payload for queue submission.
    
    Attributes:
        metadata: Task metadata for tracking.
        operation: Operation to perform.
        parameters: Operation parameters.
        context: Optional execution context.
    """
    
    metadata: TaskMetadata
    operation: str
    parameters: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary.
        
        Returns:
            Dictionary representation of payload.
        """
        return {
            "metadata": self.metadata.to_dict(),
            "operation": self.operation,
            "parameters": self.parameters,
            "context": self.context,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskPayload":
        """Create payload from dictionary.
        
        Args:
            data: Dictionary with payload fields.
            
        Returns:
            TaskPayload instance.
        """
        return cls(
            metadata=TaskMetadata.from_dict(data.get("metadata", {})),
            operation=data.get("operation", ""),
            parameters=data.get("parameters", {}),
            context=data.get("context", {}),
        )


@dataclass
class TaskResult:
    """Result from task execution.
    
    Attributes:
        task_id: Task identifier.
        status: Final task status.
        output: Task output data.
        error: Optional error message.
        duration_seconds: Execution duration.
        metadata: Additional result metadata.
    """
    
    task_id: str
    status: TaskStatus
    output: Any = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        """Check if task completed successfully.
        
        Returns:
            True if status is SUCCESS.
        """
        return self.status == TaskStatus.SUCCESS
    
    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary.
        
        Returns:
            Dictionary representation of result.
        """
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }


if __name__ == "__main__":
    metadata = TaskMetadata(
        project_id="proj-123",
        task_type=TaskType.AGENT_EXECUTION,
        priority=TaskPriority.HIGH,
    )
    print(f"Task ID: {metadata.task_id}")
    print(f"Is terminal: {metadata.is_terminal}")
    print(f"Can retry: {metadata.can_retry}")
    
    payload = TaskPayload(
        metadata=metadata,
        operation="implement_endpoint",
        parameters={"endpoint": "/api/users", "method": "GET"},
    )
    print(f"Payload: {payload.to_dict()}")
