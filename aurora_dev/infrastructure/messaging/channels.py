"""
Channel management for AURORA-DEV messaging system.

Provides channel creation, management, and routing
for the inter-agent communication system.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


logger = logging.getLogger(__name__)


class ChannelType(Enum):
    """Types of communication channels.
    
    Categorizes channels for routing and access control.
    """
    
    AGENT = "agent"
    PROJECT = "project"
    WORKFLOW = "workflow"
    BROADCAST = "broadcast"
    SYSTEM = "system"
    NOTIFICATIONS = "notifications"


@dataclass
class Channel:
    """A messaging channel.
    
    Attributes:
        name: Channel name.
        channel_type: Type of channel.
        description: Channel description.
        created_at: Creation timestamp.
        subscribers: List of subscriber IDs.
        message_count: Total messages sent.
        is_active: Whether channel is active.
        metadata: Additional metadata.
    """
    
    name: str
    channel_type: ChannelType = ChannelType.BROADCAST
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    subscribers: list[str] = field(default_factory=list)
    message_count: int = 0
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def subscriber_count(self) -> int:
        """Get number of subscribers.
        
        Returns:
            Number of subscribers.
        """
        return len(self.subscribers)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "name": self.name,
            "channel_type": self.channel_type.value,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "subscriber_count": self.subscriber_count,
            "message_count": self.message_count,
            "is_active": self.is_active,
            "metadata": self.metadata,
        }


class ChannelManager:
    """Manager for messaging channels.
    
    Handles channel creation, subscription, and routing.
    
    Attributes:
        channels: Active channels.
    """
    
    def __init__(self) -> None:
        """Initialize the channel manager."""
        self.channels: dict[str, Channel] = {}
        
        self._create_default_channels()
        
        logger.info("ChannelManager initialized")
    
    def _create_default_channels(self) -> None:
        """Create default system channels."""
        default_channels = [
            Channel(
                name="system",
                channel_type=ChannelType.SYSTEM,
                description="System-wide notifications and events",
            ),
            Channel(
                name="notifications",
                channel_type=ChannelType.NOTIFICATIONS,
                description="General notifications",
            ),
            Channel(
                name="maestro",
                channel_type=ChannelType.AGENT,
                description="Maestro orchestrator channel",
            ),
        ]
        
        for channel in default_channels:
            self.channels[channel.name] = channel
    
    def create_channel(
        self,
        name: str,
        channel_type: ChannelType = ChannelType.BROADCAST,
        description: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> Channel:
        """Create a new channel.
        
        Args:
            name: Channel name.
            channel_type: Type of channel.
            description: Channel description.
            metadata: Additional metadata.
            
        Returns:
            Created channel.
            
        Raises:
            ValueError: If channel already exists.
        """
        if name in self.channels:
            raise ValueError(f"Channel already exists: {name}")
        
        channel = Channel(
            name=name,
            channel_type=channel_type,
            description=description,
            metadata=metadata or {},
        )
        
        self.channels[name] = channel
        
        logger.info(f"Created channel: {name}")
        
        return channel
    
    def get_channel(self, name: str) -> Optional[Channel]:
        """Get a channel by name.
        
        Args:
            name: Channel name.
            
        Returns:
            Channel or None.
        """
        return self.channels.get(name)
    
    def delete_channel(self, name: str) -> bool:
        """Delete a channel.
        
        Args:
            name: Channel name.
            
        Returns:
            True if channel was deleted.
        """
        if name not in self.channels:
            return False
        
        if self.channels[name].channel_type == ChannelType.SYSTEM:
            logger.warning(f"Cannot delete system channel: {name}")
            return False
        
        del self.channels[name]
        
        logger.info(f"Deleted channel: {name}")
        
        return True
    
    def add_subscriber(
        self,
        channel_name: str,
        subscriber_id: str,
    ) -> bool:
        """Add a subscriber to a channel.
        
        Args:
            channel_name: Channel name.
            subscriber_id: Subscriber ID.
            
        Returns:
            True if subscriber was added.
        """
        channel = self.channels.get(channel_name)
        if channel is None:
            return False
        
        if subscriber_id not in channel.subscribers:
            channel.subscribers.append(subscriber_id)
            logger.debug(f"Added subscriber {subscriber_id} to {channel_name}")
        
        return True
    
    def remove_subscriber(
        self,
        channel_name: str,
        subscriber_id: str,
    ) -> bool:
        """Remove a subscriber from a channel.
        
        Args:
            channel_name: Channel name.
            subscriber_id: Subscriber ID.
            
        Returns:
            True if subscriber was removed.
        """
        channel = self.channels.get(channel_name)
        if channel is None:
            return False
        
        if subscriber_id in channel.subscribers:
            channel.subscribers.remove(subscriber_id)
            logger.debug(f"Removed subscriber {subscriber_id} from {channel_name}")
            return True
        
        return False
    
    def get_agent_channel(self, agent_id: str) -> str:
        """Get or create an agent's direct channel.
        
        Args:
            agent_id: Agent identifier.
            
        Returns:
            Channel name.
        """
        channel_name = f"agent:{agent_id}"
        
        if channel_name not in self.channels:
            self.create_channel(
                name=channel_name,
                channel_type=ChannelType.AGENT,
                description=f"Direct channel for agent {agent_id}",
            )
        
        return channel_name
    
    def get_project_channel(self, project_id: str) -> str:
        """Get or create a project's channel.
        
        Args:
            project_id: Project identifier.
            
        Returns:
            Channel name.
        """
        channel_name = f"project:{project_id}"
        
        if channel_name not in self.channels:
            self.create_channel(
                name=channel_name,
                channel_type=ChannelType.PROJECT,
                description=f"Channel for project {project_id}",
            )
        
        return channel_name
    
    def get_workflow_channel(self, workflow_id: str) -> str:
        """Get or create a workflow's channel.
        
        Args:
            workflow_id: Workflow identifier.
            
        Returns:
            Channel name.
        """
        channel_name = f"workflow:{workflow_id}"
        
        if channel_name not in self.channels:
            self.create_channel(
                name=channel_name,
                channel_type=ChannelType.WORKFLOW,
                description=f"Channel for workflow {workflow_id}",
            )
        
        return channel_name
    
    def list_channels(
        self,
        channel_type: Optional[ChannelType] = None,
        active_only: bool = True,
    ) -> list[Channel]:
        """List channels with optional filtering.
        
        Args:
            channel_type: Filter by channel type.
            active_only: Only return active channels.
            
        Returns:
            List of matching channels.
        """
        channels = list(self.channels.values())
        
        if channel_type:
            channels = [c for c in channels if c.channel_type == channel_type]
        
        if active_only:
            channels = [c for c in channels if c.is_active]
        
        return channels
    
    def get_subscriber_channels(
        self,
        subscriber_id: str,
    ) -> list[str]:
        """Get all channels a subscriber is subscribed to.
        
        Args:
            subscriber_id: Subscriber ID.
            
        Returns:
            List of channel names.
        """
        return [
            name for name, channel in self.channels.items()
            if subscriber_id in channel.subscribers
        ]
    
    def record_message(self, channel_name: str) -> None:
        """Record a message sent to a channel.
        
        Args:
            channel_name: Channel name.
        """
        channel = self.channels.get(channel_name)
        if channel:
            channel.message_count += 1
    
    def get_statistics(self) -> dict[str, Any]:
        """Get channel statistics.
        
        Returns:
            Dictionary with statistics.
        """
        channels = list(self.channels.values())
        
        by_type = {}
        for channel in channels:
            t = channel.channel_type.value
            by_type[t] = by_type.get(t, 0) + 1
        
        total_messages = sum(c.message_count for c in channels)
        total_subscribers = sum(c.subscriber_count for c in channels)
        
        return {
            "total_channels": len(channels),
            "active_channels": sum(1 for c in channels if c.is_active),
            "by_type": by_type,
            "total_messages": total_messages,
            "total_subscribers": total_subscribers,
        }


if __name__ == "__main__":
    manager = ChannelManager()
    
    channel = manager.create_channel(
        name="test-channel",
        channel_type=ChannelType.BROADCAST,
        description="Test channel",
    )
    print(f"Created: {channel.to_dict()}")
    
    manager.add_subscriber("test-channel", "agent-1")
    manager.add_subscriber("test-channel", "agent-2")
    
    agent_channel = manager.get_agent_channel("backend-1")
    print(f"Agent channel: {agent_channel}")
    
    print(f"Stats: {manager.get_statistics()}")
