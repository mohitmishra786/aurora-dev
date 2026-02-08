"""
Message Broker for AURORA-DEV inter-agent communication.

Provides a Redis-based pub/sub messaging system for
asynchronous inter-agent communication.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from uuid import uuid4

import redis.asyncio as aioredis

from aurora_dev.core.config import get_settings
from aurora_dev.infrastructure.messaging.messages import (
    Message,
    MessagePriority,
    MessageType,
)


logger = logging.getLogger(__name__)


MessageHandler = Callable[[Message], None]
AsyncMessageHandler = Callable[[Message], Any]


@dataclass
class Subscription:
    """Subscription to a message channel.
    
    Attributes:
        subscription_id: Unique subscription identifier.
        channel: Channel pattern subscribed to.
        handler: Message handler function.
        is_async: Whether handler is async.
        created_at: Subscription creation timestamp.
        messages_received: Count of messages received.
    """
    
    subscription_id: str = field(default_factory=lambda: str(uuid4()))
    channel: str = ""
    handler: Optional[MessageHandler] = None
    async_handler: Optional[AsyncMessageHandler] = None
    is_async: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    messages_received: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "subscription_id": self.subscription_id,
            "channel": self.channel,
            "is_async": self.is_async,
            "created_at": self.created_at.isoformat(),
            "messages_received": self.messages_received,
        }


class MessageBroker:
    """Redis-based message broker for inter-agent communication.
    
    Provides publish/subscribe functionality for agents to
    communicate asynchronously.
    
    Attributes:
        subscriptions: Active subscriptions.
        message_history: Recent message history.
        history_size: Maximum history size.
    """
    
    def __init__(
        self,
        history_size: int = 1000,
    ) -> None:
        """Initialize the message broker.
        
        Args:
            history_size: Maximum messages to keep in history.
        """
        self._settings = get_settings()
        self._redis: Optional[aioredis.Redis] = None
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._prefix = "aurora:msg:"
        self._running = False
        
        self.subscriptions: dict[str, Subscription] = {}
        self.message_history: list[Message] = []
        self.history_size = history_size
        self._handlers: dict[str, list[Subscription]] = {}
        
        logger.info("MessageBroker initialized")
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._redis = aioredis.from_url(
                self._settings.redis.url,
                decode_responses=True,
            )
            self._pubsub = self._redis.pubsub()
            logger.info("MessageBroker connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        self._running = False
        
        if self._pubsub:
            await self._pubsub.close()
        
        if self._redis:
            await self._redis.close()
        
        logger.info("MessageBroker disconnected")
    
    async def publish(
        self,
        message: Message,
    ) -> bool:
        """Publish a message to a channel.
        
        Args:
            message: Message to publish.
            
        Returns:
            True if message was published.
        """
        if self._redis is None:
            logger.warning("Broker not connected, message not published")
            return False
        
        if message.is_expired:
            logger.debug(f"Message expired, not publishing: {message.message_id}")
            return False
        
        try:
            channel = f"{self._prefix}{message.channel}"
            payload = json.dumps(message.to_dict())
            
            await self._redis.publish(channel, payload)
            
            self._add_to_history(message)
            
            logger.debug(f"Published message {message.message_id} to {channel}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False
    
    async def subscribe(
        self,
        channel: str,
        handler: MessageHandler,
    ) -> str:
        """Subscribe to a channel.
        
        Args:
            channel: Channel to subscribe to.
            handler: Message handler function.
            
        Returns:
            Subscription ID.
        """
        subscription = Subscription(
            channel=channel,
            handler=handler,
            is_async=False,
        )
        
        self.subscriptions[subscription.subscription_id] = subscription
        
        if channel not in self._handlers:
            self._handlers[channel] = []
        self._handlers[channel].append(subscription)
        
        if self._pubsub:
            await self._pubsub.subscribe(f"{self._prefix}{channel}")
        
        logger.info(f"Subscribed to channel: {channel}")
        
        return subscription.subscription_id
    
    async def subscribe_async(
        self,
        channel: str,
        handler: AsyncMessageHandler,
    ) -> str:
        """Subscribe to a channel with async handler.
        
        Args:
            channel: Channel to subscribe to.
            handler: Async message handler function.
            
        Returns:
            Subscription ID.
        """
        subscription = Subscription(
            channel=channel,
            async_handler=handler,
            is_async=True,
        )
        
        self.subscriptions[subscription.subscription_id] = subscription
        
        if channel not in self._handlers:
            self._handlers[channel] = []
        self._handlers[channel].append(subscription)
        
        if self._pubsub:
            await self._pubsub.subscribe(f"{self._prefix}{channel}")
        
        logger.info(f"Subscribed (async) to channel: {channel}")
        
        return subscription.subscription_id
    
    async def unsubscribe(
        self,
        subscription_id: str,
    ) -> bool:
        """Unsubscribe from a channel.
        
        Args:
            subscription_id: Subscription ID.
            
        Returns:
            True if unsubscribed.
        """
        subscription = self.subscriptions.get(subscription_id)
        if subscription is None:
            return False
        
        channel = subscription.channel
        
        if channel in self._handlers:
            self._handlers[channel] = [
                s for s in self._handlers[channel]
                if s.subscription_id != subscription_id
            ]
            
            if not self._handlers[channel]:
                del self._handlers[channel]
                if self._pubsub:
                    await self._pubsub.unsubscribe(f"{self._prefix}{channel}")
        
        del self.subscriptions[subscription_id]
        
        logger.info(f"Unsubscribed: {subscription_id}")
        
        return True
    
    async def start_listening(self) -> None:
        """Start listening for messages."""
        if self._pubsub is None:
            logger.error("Broker not connected")
            return
        
        self._running = True
        
        logger.info("MessageBroker listening for messages")
        
        while self._running:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                
                if message:
                    await self._handle_message(message)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message listener: {e}")
                await asyncio.sleep(1)
    
    async def _handle_message(
        self,
        raw_message: dict[str, Any],
    ) -> None:
        """Handle an incoming message.
        
        Args:
            raw_message: Raw Redis message.
        """
        try:
            channel = raw_message.get("channel", "").replace(self._prefix, "")
            data = raw_message.get("data", "")
            
            if not isinstance(data, str):
                return
            
            message = Message.from_dict(json.loads(data))
            
            handlers = self._handlers.get(channel, [])
            
            for subscription in handlers:
                subscription.messages_received += 1
                
                try:
                    if subscription.is_async and subscription.async_handler:
                        await subscription.async_handler(message)
                    elif subscription.handler:
                        subscription.handler(message)
                except Exception as e:
                    logger.error(f"Handler error: {e}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"Invalid message JSON: {e}")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
    
    def _add_to_history(self, message: Message) -> None:
        """Add message to history.
        
        Args:
            message: Message to add.
        """
        self.message_history.append(message)
        
        if len(self.message_history) > self.history_size:
            self.message_history = self.message_history[-self.history_size:]
    
    async def send_direct(
        self,
        recipient_id: str,
        message: Message,
    ) -> bool:
        """Send a message directly to an agent.
        
        Args:
            recipient_id: Recipient agent ID.
            message: Message to send.
            
        Returns:
            True if message was sent.
        """
        message.recipient_id = recipient_id
        message.channel = f"agent:{recipient_id}"
        
        return await self.publish(message)
    
    async def broadcast(
        self,
        channel: str,
        payload: dict[str, Any],
        sender_id: str = "system",
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> bool:
        """Broadcast a message to a channel.
        
        Args:
            channel: Channel to broadcast to.
            payload: Message payload.
            sender_id: Sender ID.
            priority: Message priority.
            
        Returns:
            True if broadcast was sent.
        """
        message = Message(
            message_type=MessageType.BROADCAST,
            sender_id=sender_id,
            channel=channel,
            payload=payload,
            priority=priority,
        )
        
        return await self.publish(message)
    
    async def request_response(
        self,
        message: Message,
        timeout_seconds: float = 30.0,
    ) -> Optional[Message]:
        """Send a request and wait for response.
        
        Args:
            message: Request message.
            timeout_seconds: Timeout for response.
            
        Returns:
            Response message or None.
        """
        correlation_id = message.correlation_id or str(uuid4())
        message.correlation_id = correlation_id
        
        response_channel = f"response:{correlation_id}"
        response: Optional[Message] = None
        received = asyncio.Event()
        
        async def response_handler(msg: Message) -> None:
            nonlocal response
            if msg.correlation_id == correlation_id:
                response = msg
                received.set()
        
        await self.subscribe_async(response_channel, response_handler)
        
        try:
            await self.publish(message)
            
            await asyncio.wait_for(received.wait(), timeout=timeout_seconds)
            
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout: {correlation_id}")
            return None
        finally:
            subs = [
                sid for sid, sub in self.subscriptions.items()
                if sub.channel == response_channel
            ]
            for sid in subs:
                await self.unsubscribe(sid)
    
    def get_statistics(self) -> dict[str, Any]:
        """Get broker statistics.
        
        Returns:
            Dictionary with statistics.
        """
        total_received = sum(
            s.messages_received for s in self.subscriptions.values()
        )
        
        return {
            "subscriptions": len(self.subscriptions),
            "channels": len(self._handlers),
            "history_size": len(self.message_history),
            "total_messages_received": total_received,
            "is_connected": self._redis is not None,
            "is_running": self._running,
        }


if __name__ == "__main__":
    async def main():
        broker = MessageBroker()
        await broker.connect()
        
        def handler(msg: Message):
            print(f"Received: {msg.message_id}")
        
        await broker.subscribe("test", handler)
        
        msg = Message(
            sender_id="test-sender",
            channel="test",
            payload={"hello": "world"},
        )
        await broker.publish(msg)
        
        print(f"Stats: {broker.get_statistics()}")
        
        await broker.disconnect()
    
    asyncio.run(main())
