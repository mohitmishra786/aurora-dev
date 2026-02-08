"""
Inter-Agent Messaging System for AURORA-DEV.

This package provides a pub/sub messaging system for
inter-agent communication using Redis.
"""
from aurora_dev.infrastructure.messaging.broker import MessageBroker
from aurora_dev.infrastructure.messaging.messages import (
    Message,
    MessageType,
    TaskAssignment,
    TaskResult,
    AgentNotification,
)
from aurora_dev.infrastructure.messaging.channels import ChannelManager

__all__ = [
    "MessageBroker",
    "Message",
    "MessageType",
    "TaskAssignment",
    "TaskResult",
    "AgentNotification",
    "ChannelManager",
]
