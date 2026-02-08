"""
Message type definitions for AURORA-DEV inter-agent communication.

Provides message types, serialization, and validation for
the messaging system.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class MessageType(Enum):
    """Types of messages in the system.
    
    Categorizes messages for routing and handling.
    """
    
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    TASK_PROGRESS = "task_progress"
    AGENT_NOTIFICATION = "agent_notification"
    AGENT_STATUS = "agent_status"
    REFLEXION_REQUEST = "reflexion_request"
    REFLEXION_RESPONSE = "reflexion_response"
    MEMORY_UPDATE = "memory_update"
    WORKFLOW_EVENT = "workflow_event"
    SYSTEM = "system"
    BROADCAST = "broadcast"


class MessagePriority(Enum):
    """Message priority levels.
    
    Determines processing order for messages.
    """
    
    LOW = 1
    NORMAL = 5
    HIGH = 7
    URGENT = 10


@dataclass
class Message:
    """Base message for inter-agent communication.
    
    Attributes:
        message_id: Unique message identifier.
        message_type: Type of message.
        sender_id: Sender agent/component ID.
        recipient_id: Optional recipient ID (None for broadcast).
        channel: Channel for routing.
        payload: Message payload.
        priority: Message priority.
        created_at: Message creation timestamp.
        expires_at: Optional expiration timestamp.
        correlation_id: Optional correlation ID for request/response.
        metadata: Additional metadata.
    """
    
    message_id: str = field(default_factory=lambda: str(uuid4()))
    message_type: MessageType = MessageType.SYSTEM
    sender_id: str = ""
    recipient_id: Optional[str] = None
    channel: str = "default"
    payload: dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    correlation_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """Check if message has expired.
        
        Returns:
            True if message is expired.
        """
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_broadcast(self) -> bool:
        """Check if message is a broadcast.
        
        Returns:
            True if no specific recipient.
        """
        return self.recipient_id is None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "channel": self.channel,
            "payload": self.payload,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create message from dictionary.
        
        Args:
            data: Dictionary data.
            
        Returns:
            Message instance.
        """
        return cls(
            message_id=data.get("message_id", str(uuid4())),
            message_type=MessageType(data.get("message_type", "system")),
            sender_id=data.get("sender_id", ""),
            recipient_id=data.get("recipient_id"),
            channel=data.get("channel", "default"),
            payload=data.get("payload", {}),
            priority=MessagePriority(data.get("priority", 5)),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TaskAssignment(Message):
    """Message for assigning a task to an agent.
    
    Attributes:
        task_id: Task identifier.
        operation: Operation to perform.
        parameters: Operation parameters.
        deadline: Optional deadline.
    """
    
    task_id: str = ""
    operation: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    deadline: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """Set message type after initialization."""
        self.message_type = MessageType.TASK_ASSIGNMENT
        self.payload = {
            "task_id": self.task_id,
            "operation": self.operation,
            "parameters": self.parameters,
            "deadline": self.deadline.isoformat() if self.deadline else None,
        }
    
    @classmethod
    def create(
        cls,
        sender_id: str,
        recipient_id: str,
        task_id: str,
        operation: str,
        parameters: Optional[dict[str, Any]] = None,
        deadline: Optional[datetime] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> "TaskAssignment":
        """Create a task assignment message.
        
        Args:
            sender_id: Sender agent ID.
            recipient_id: Recipient agent ID.
            task_id: Task identifier.
            operation: Operation to perform.
            parameters: Operation parameters.
            deadline: Optional deadline.
            priority: Message priority.
            
        Returns:
            TaskAssignment instance.
        """
        return cls(
            sender_id=sender_id,
            recipient_id=recipient_id,
            channel=f"agent:{recipient_id}",
            task_id=task_id,
            operation=operation,
            parameters=parameters or {},
            deadline=deadline,
            priority=priority,
        )


@dataclass
class TaskResult(Message):
    """Message containing task execution result.
    
    Attributes:
        task_id: Task identifier.
        success: Whether task succeeded.
        output: Task output.
        error: Optional error message.
        duration_seconds: Execution duration.
    """
    
    task_id: str = ""
    success: bool = False
    output: Any = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    
    def __post_init__(self) -> None:
        """Set message type after initialization."""
        self.message_type = MessageType.TASK_RESULT
        self.payload = {
            "task_id": self.task_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }
    
    @classmethod
    def create(
        cls,
        sender_id: str,
        recipient_id: str,
        task_id: str,
        success: bool,
        output: Any = None,
        error: Optional[str] = None,
        duration_seconds: float = 0.0,
        correlation_id: Optional[str] = None,
    ) -> "TaskResult":
        """Create a task result message.
        
        Args:
            sender_id: Sender agent ID.
            recipient_id: Recipient agent ID.
            task_id: Task identifier.
            success: Whether task succeeded.
            output: Task output.
            error: Optional error message.
            duration_seconds: Execution duration.
            correlation_id: Optional correlation ID.
            
        Returns:
            TaskResult instance.
        """
        return cls(
            sender_id=sender_id,
            recipient_id=recipient_id,
            channel=f"agent:{recipient_id}",
            task_id=task_id,
            success=success,
            output=output,
            error=error,
            duration_seconds=duration_seconds,
            correlation_id=correlation_id,
        )


@dataclass
class AgentNotification(Message):
    """Notification message for agent events.
    
    Attributes:
        notification_type: Type of notification.
        title: Notification title.
        body: Notification body.
        level: Severity level (info, warning, error).
    """
    
    notification_type: str = "info"
    title: str = ""
    body: str = ""
    level: str = "info"
    
    def __post_init__(self) -> None:
        """Set message type after initialization."""
        self.message_type = MessageType.AGENT_NOTIFICATION
        self.payload = {
            "notification_type": self.notification_type,
            "title": self.title,
            "body": self.body,
            "level": self.level,
        }
    
    @classmethod
    def create(
        cls,
        sender_id: str,
        recipient_id: Optional[str],
        title: str,
        body: str,
        level: str = "info",
        channel: str = "notifications",
    ) -> "AgentNotification":
        """Create an agent notification.
        
        Args:
            sender_id: Sender agent ID.
            recipient_id: Optional recipient ID.
            title: Notification title.
            body: Notification body.
            level: Severity level.
            channel: Channel for routing.
            
        Returns:
            AgentNotification instance.
        """
        return cls(
            sender_id=sender_id,
            recipient_id=recipient_id,
            channel=channel,
            title=title,
            body=body,
            level=level,
        )


@dataclass
class ReflexionRequest(Message):
    """Request for reflexion processing.
    
    Attributes:
        task_id: Original task ID.
        attempt_number: Attempt number.
        error: Error that triggered reflexion.
        context: Previous attempt context.
    """
    
    task_id: str = ""
    attempt_number: int = 1
    error: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Set message type after initialization."""
        self.message_type = MessageType.REFLEXION_REQUEST
        self.payload = {
            "task_id": self.task_id,
            "attempt_number": self.attempt_number,
            "error": self.error,
            "context": self.context,
        }


@dataclass
class MemoryUpdate(Message):
    """Message for memory system updates.
    
    Attributes:
        memory_type: Type of memory (short_term, long_term, episodic).
        action: Action performed (store, retrieve, prune).
        content: Memory content.
        tags: Memory tags.
    """
    
    memory_type: str = "short_term"
    action: str = "store"
    content: str = ""
    tags: list[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Set message type after initialization."""
        self.message_type = MessageType.MEMORY_UPDATE
        self.payload = {
            "memory_type": self.memory_type,
            "action": self.action,
            "content": self.content,
            "tags": self.tags,
        }


def create_broadcast(
    sender_id: str,
    channel: str,
    payload: dict[str, Any],
    priority: MessagePriority = MessagePriority.NORMAL,
) -> Message:
    """Create a broadcast message.
    
    Args:
        sender_id: Sender ID.
        channel: Broadcast channel.
        payload: Message payload.
        priority: Message priority.
        
    Returns:
        Broadcast message.
    """
    return Message(
        message_type=MessageType.BROADCAST,
        sender_id=sender_id,
        channel=channel,
        payload=payload,
        priority=priority,
    )


if __name__ == "__main__":
    assignment = TaskAssignment.create(
        sender_id="maestro-1",
        recipient_id="backend-1",
        task_id="task-123",
        operation="implement_endpoint",
        parameters={"endpoint": "/api/users"},
    )
    print(f"Assignment: {assignment.to_dict()}")
    
    result = TaskResult.create(
        sender_id="backend-1",
        recipient_id="maestro-1",
        task_id="task-123",
        success=True,
        output={"code": "..."},
    )
    print(f"Result: {result.to_dict()}")
