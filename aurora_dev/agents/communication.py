"""
Agent Communication Protocol for AURORA-DEV.

This module defines the standardized message format and protocols
for inter-agent communication, including message types, routing,
and queue-based messaging.
"""
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from aurora_dev.agents.base_agent import AgentRole
from aurora_dev.core.logging import get_logger

logger = get_logger("communication")


class MessageType(Enum):
    """Types of inter-agent messages."""
    
    # Task Management
    TASK_ASSIGN = "task_assign"
    TASK_ACCEPT = "task_accept"
    TASK_REJECT = "task_reject"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    TASK_PROGRESS = "task_progress"
    
    # Coordination
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    QUERY = "query"
    
    # Control
    PAUSE = "pause"
    RESUME = "resume"
    TERMINATE = "terminate"
    HEARTBEAT = "heartbeat"
    
    # Collaboration
    HANDOFF = "handoff"
    REVIEW_REQUEST = "review_request"
    REVIEW_RESPONSE = "review_response"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_RESPONSE = "approval_response"


class MessagePriority(Enum):
    """Message priority levels."""
    
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class AgentMessage:
    """
    Standardized message format for agent communication.
    
    Attributes:
        id: Unique message identifier.
        type: Message type.
        sender_id: ID of the sending agent.
        sender_role: Role of the sending agent.
        recipient_id: ID of the recipient agent (None for broadcast).
        recipient_role: Target role (for role-based routing).
        content: Message content (any JSON-serializable data).
        priority: Message priority.
        correlation_id: ID linking related messages.
        reply_to: ID of message being replied to.
        timestamp: Message creation timestamp.
        expires_at: Optional expiration timestamp.
        metadata: Additional metadata.
    """
    
    type: MessageType
    sender_id: str
    sender_role: AgentRole
    content: Any
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recipient_id: Optional[str] = None
    recipient_role: Optional[AgentRole] = None
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        data = asdict(self)
        data["type"] = self.type.value
        data["sender_role"] = self.sender_role.value
        data["priority"] = self.priority.value
        data["timestamp"] = self.timestamp.isoformat()
        
        if self.recipient_role:
            data["recipient_role"] = self.recipient_role.value
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
            
        return data
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary."""
        data["type"] = MessageType(data["type"])
        data["sender_role"] = AgentRole(data["sender_role"])
        data["priority"] = MessagePriority(data.get("priority", 1))
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        
        if data.get("recipient_role"):
            data["recipient_role"] = AgentRole(data["recipient_role"])
        if data.get("expires_at"):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
            
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "AgentMessage":
        """Create message from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def is_expired(self) -> bool:
        """Check if message has expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def create_reply(
        self,
        type: MessageType,
        sender_id: str,
        sender_role: AgentRole,
        content: Any,
        **kwargs,
    ) -> "AgentMessage":
        """Create a reply to this message."""
        return AgentMessage(
            type=type,
            sender_id=sender_id,
            sender_role=sender_role,
            recipient_id=self.sender_id,
            recipient_role=self.sender_role,
            content=content,
            correlation_id=self.correlation_id or self.id,
            reply_to=self.id,
            **kwargs,
        )


class MessageQueue:
    """
    In-memory message queue for agent communication.
    
    Provides thread-safe message queueing with priority ordering.
    For production, this should be backed by Redis or similar.
    """
    
    def __init__(self, max_size: int = 10000) -> None:
        """
        Initialize the message queue.
        
        Args:
            max_size: Maximum queue size.
        """
        import heapq
        from threading import Lock
        
        self._queue: list[tuple[int, float, AgentMessage]] = []
        self._max_size = max_size
        self._lock = Lock()
        self._message_count = 0
        
    def push(self, message: AgentMessage) -> bool:
        """
        Add a message to the queue.
        
        Args:
            message: The message to queue.
            
        Returns:
            True if message was queued, False if queue is full.
        """
        import heapq
        
        with self._lock:
            if len(self._queue) >= self._max_size:
                logger.warning("Message queue full, dropping message")
                return False
            
            # Priority queue: (priority, timestamp, message)
            # Negate priority so higher priority = lower number = comes first
            priority = -message.priority.value
            timestamp = message.timestamp.timestamp()
            
            heapq.heappush(self._queue, (priority, timestamp, message))
            self._message_count += 1
            
            logger.debug(
                f"Message queued: {message.type.value}",
                extra={"message_id": message.id},
            )
            return True
    
    def pop(self) -> Optional[AgentMessage]:
        """
        Get the next message from the queue.
        
        Returns:
            The next message, or None if queue is empty.
        """
        import heapq
        
        with self._lock:
            if not self._queue:
                return None
            
            _, _, message = heapq.heappop(self._queue)
            
            # Skip expired messages
            if message.is_expired():
                logger.debug(
                    f"Skipping expired message: {message.id}",
                )
                return self.pop()
            
            return message
    
    def peek(self) -> Optional[AgentMessage]:
        """
        Peek at the next message without removing it.
        
        Returns:
            The next message, or None if queue is empty.
        """
        with self._lock:
            if not self._queue:
                return None
            return self._queue[0][2]
    
    def size(self) -> int:
        """Get the current queue size."""
        return len(self._queue)
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._queue) == 0
    
    def clear(self) -> int:
        """
        Clear all messages from the queue.
        
        Returns:
            Number of messages cleared.
        """
        with self._lock:
            count = len(self._queue)
            self._queue.clear()
            logger.info(f"Queue cleared, removed {count} messages")
            return count
    
    def get_stats(self) -> dict[str, Any]:
        """Get queue statistics."""
        return {
            "size": self.size(),
            "max_size": self._max_size,
            "total_messages": self._message_count,
        }


class MessageBroker:
    """
    Message broker for routing messages between agents.
    
    Manages message queues per agent and handles routing
    based on recipient ID, role, or broadcast.
    """
    
    def __init__(self) -> None:
        """Initialize the message broker."""
        from threading import Lock
        
        self._agent_queues: dict[str, MessageQueue] = {}
        self._role_subscribers: dict[AgentRole, set[str]] = {}
        self._lock = Lock()
        
        logger.info("Message broker initialized")
    
    def register_agent(
        self, agent_id: str, role: AgentRole, queue_size: int = 1000
    ) -> MessageQueue:
        """
        Register an agent with the broker.
        
        Args:
            agent_id: The agent's unique ID.
            role: The agent's role.
            queue_size: Maximum queue size for this agent.
            
        Returns:
            The agent's message queue.
        """
        with self._lock:
            if agent_id not in self._agent_queues:
                self._agent_queues[agent_id] = MessageQueue(queue_size)
            
            # Subscribe to role-based messages
            if role not in self._role_subscribers:
                self._role_subscribers[role] = set()
            self._role_subscribers[role].add(agent_id)
            
            logger.info(
                f"Agent registered with broker",
                extra={"agent_id": agent_id, "role": role.value},
            )
            
            return self._agent_queues[agent_id]
    
    def unregister_agent(self, agent_id: str, role: AgentRole) -> None:
        """
        Unregister an agent from the broker.
        
        Args:
            agent_id: The agent's unique ID.
            role: The agent's role.
        """
        with self._lock:
            self._agent_queues.pop(agent_id, None)
            
            if role in self._role_subscribers:
                self._role_subscribers[role].discard(agent_id)
                if not self._role_subscribers[role]:
                    del self._role_subscribers[role]
            
            logger.info(
                f"Agent unregistered from broker",
                extra={"agent_id": agent_id},
            )
    
    def send(self, message: AgentMessage) -> int:
        """
        Send a message to its recipient(s).
        
        Args:
            message: The message to send.
            
        Returns:
            Number of recipients the message was delivered to.
        """
        delivered = 0
        
        with self._lock:
            # Direct message to specific agent
            if message.recipient_id:
                queue = self._agent_queues.get(message.recipient_id)
                if queue and queue.push(message):
                    delivered += 1
            
            # Role-based message
            elif message.recipient_role:
                agent_ids = self._role_subscribers.get(message.recipient_role, set())
                for agent_id in agent_ids:
                    queue = self._agent_queues.get(agent_id)
                    if queue and queue.push(message):
                        delivered += 1
            
            # Broadcast (goes to all agents except sender)
            elif message.type == MessageType.BROADCAST:
                for agent_id, queue in self._agent_queues.items():
                    if agent_id != message.sender_id:
                        if queue.push(message):
                            delivered += 1
        
        logger.debug(
            f"Message sent to {delivered} recipient(s)",
            extra={"message_id": message.id, "type": message.type.value},
        )
        
        return delivered
    
    def receive(self, agent_id: str) -> Optional[AgentMessage]:
        """
        Receive the next message for an agent.
        
        Args:
            agent_id: The agent's unique ID.
            
        Returns:
            The next message, or None if queue is empty.
        """
        queue = self._agent_queues.get(agent_id)
        if queue:
            return queue.pop()
        return None
    
    def get_queue(self, agent_id: str) -> Optional[MessageQueue]:
        """Get an agent's message queue."""
        return self._agent_queues.get(agent_id)
    
    def get_stats(self) -> dict[str, Any]:
        """Get broker statistics."""
        total_queued = sum(q.size() for q in self._agent_queues.values())
        return {
            "registered_agents": len(self._agent_queues),
            "total_messages_queued": total_queued,
            "roles_with_subscribers": list(self._role_subscribers.keys()),
        }


# Global broker instance
_broker: Optional[MessageBroker] = None


def get_broker() -> MessageBroker:
    """
    Get the global message broker instance.
    
    Returns:
        The MessageBroker singleton.
    """
    global _broker
    if _broker is None:
        _broker = MessageBroker()
    return _broker
