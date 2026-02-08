"""
WebSocket connection manager for real-time updates.

Provides real-time event broadcasting to connected clients
for task progress, agent status, and workflow updates.
"""
import asyncio
import json
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field

from fastapi import WebSocket, WebSocketDisconnect

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class Connection:
    """WebSocket connection with metadata."""
    
    websocket: WebSocket
    client_id: str
    project_id: Optional[str] = None
    subscriptions: set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.now)


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.
    
    Supports room-based messaging for project isolation and
    topic subscriptions for specific event types.
    """
    
    def __init__(self):
        """Initialize connection manager."""
        self._connections: dict[str, Connection] = {}
        self._project_rooms: dict[str, set[str]] = {}
        self._logger = get_logger(__name__)
    
    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        project_id: Optional[str] = None,
    ) -> Connection:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection.
            client_id: Unique client identifier.
            project_id: Optional project to join.
            
        Returns:
            Connection object.
        """
        await websocket.accept()
        
        connection = Connection(
            websocket=websocket,
            client_id=client_id,
            project_id=project_id,
        )
        
        self._connections[client_id] = connection
        
        # Join project room if specified
        if project_id:
            await self.join_project(client_id, project_id)
        
        self._logger.info(f"Client connected: {client_id}")
        
        return connection
    
    async def disconnect(self, client_id: str) -> None:
        """
        Handle client disconnect.
        
        Args:
            client_id: The client to disconnect.
        """
        if client_id not in self._connections:
            return
        
        connection = self._connections[client_id]
        
        # Leave all project rooms
        if connection.project_id:
            await self.leave_project(client_id, connection.project_id)
        
        del self._connections[client_id]
        
        self._logger.info(f"Client disconnected: {client_id}")
    
    async def join_project(self, client_id: str, project_id: str) -> None:
        """
        Join a project room for updates.
        
        Args:
            client_id: The client.
            project_id: The project to join.
        """
        if project_id not in self._project_rooms:
            self._project_rooms[project_id] = set()
        
        self._project_rooms[project_id].add(client_id)
        
        if client_id in self._connections:
            self._connections[client_id].project_id = project_id
        
        self._logger.debug(f"Client {client_id} joined project {project_id}")
    
    async def leave_project(self, client_id: str, project_id: str) -> None:
        """
        Leave a project room.
        
        Args:
            client_id: The client.
            project_id: The project to leave.
        """
        if project_id in self._project_rooms:
            self._project_rooms[project_id].discard(client_id)
            
            # Clean up empty rooms
            if not self._project_rooms[project_id]:
                del self._project_rooms[project_id]
    
    async def subscribe(self, client_id: str, topic: str) -> None:
        """
        Subscribe to a topic for updates.
        
        Args:
            client_id: The client.
            topic: The topic (e.g., 'tasks', 'agents', 'workflows').
        """
        if client_id in self._connections:
            self._connections[client_id].subscriptions.add(topic)
    
    async def unsubscribe(self, client_id: str, topic: str) -> None:
        """
        Unsubscribe from a topic.
        
        Args:
            client_id: The client.
            topic: The topic to unsubscribe from.
        """
        if client_id in self._connections:
            self._connections[client_id].subscriptions.discard(topic)
    
    async def send_personal(
        self,
        client_id: str,
        message: dict[str, Any],
    ) -> bool:
        """
        Send a message to a specific client.
        
        Args:
            client_id: The target client.
            message: The message to send.
            
        Returns:
            True if sent successfully, False otherwise.
        """
        if client_id not in self._connections:
            return False
        
        try:
            connection = self._connections[client_id]
            await connection.websocket.send_json(message)
            return True
        except Exception as e:
            self._logger.error(f"Failed to send to {client_id}: {e}")
            return False
    
    async def broadcast(
        self,
        message: dict[str, Any],
        exclude: Optional[set[str]] = None,
    ) -> int:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message to send.
            exclude: Client IDs to exclude.
            
        Returns:
            Number of clients that received the message.
        """
        exclude = exclude or set()
        sent_count = 0
        
        for client_id, connection in self._connections.items():
            if client_id in exclude:
                continue
            
            try:
                await connection.websocket.send_json(message)
                sent_count += 1
            except Exception as e:
                self._logger.error(f"Failed to broadcast to {client_id}: {e}")
        
        return sent_count
    
    async def broadcast_to_project(
        self,
        project_id: str,
        message: dict[str, Any],
        exclude: Optional[set[str]] = None,
    ) -> int:
        """
        Broadcast a message to all clients in a project room.
        
        Args:
            project_id: The project room.
            message: The message to send.
            exclude: Client IDs to exclude.
            
        Returns:
            Number of clients that received the message.
        """
        exclude = exclude or set()
        sent_count = 0
        
        if project_id not in self._project_rooms:
            return 0
        
        for client_id in self._project_rooms[project_id]:
            if client_id in exclude:
                continue
            
            if client_id in self._connections:
                try:
                    connection = self._connections[client_id]
                    await connection.websocket.send_json(message)
                    sent_count += 1
                except Exception as e:
                    self._logger.error(f"Failed to send to {client_id}: {e}")
        
        return sent_count
    
    async def broadcast_to_topic(
        self,
        topic: str,
        message: dict[str, Any],
    ) -> int:
        """
        Broadcast a message to all clients subscribed to a topic.
        
        Args:
            topic: The topic.
            message: The message to send.
            
        Returns:
            Number of clients that received the message.
        """
        sent_count = 0
        
        for client_id, connection in self._connections.items():
            if topic in connection.subscriptions:
                try:
                    await connection.websocket.send_json(message)
                    sent_count += 1
                except Exception as e:
                    self._logger.error(f"Failed to send to {client_id}: {e}")
        
        return sent_count
    
    def get_active_connections(self) -> int:
        """Get count of active connections."""
        return len(self._connections)
    
    def get_project_connections(self, project_id: str) -> int:
        """Get count of connections in a project room."""
        return len(self._project_rooms.get(project_id, set()))


# Global connection manager instance
_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get or create the global connection manager."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


# Event helper functions

async def emit_task_update(
    project_id: str,
    task_id: str,
    status: str,
    progress: int,
    metadata: Optional[dict] = None,
) -> None:
    """Emit a task update event."""
    manager = get_connection_manager()
    
    await manager.broadcast_to_project(project_id, {
        "type": "task_update",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "task_id": task_id,
            "status": status,
            "progress_percent": progress,
            **(metadata or {}),
        },
    })


async def emit_agent_update(
    agent_id: str,
    status: str,
    current_task: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    """Emit an agent status update event."""
    manager = get_connection_manager()
    
    await manager.broadcast_to_topic("agents", {
        "type": "agent_update",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "agent_id": agent_id,
            "status": status,
            "current_task": current_task,
            **(metadata or {}),
        },
    })


async def emit_workflow_update(
    project_id: str,
    workflow_id: str,
    phase: str,
    status: str,
    progress: int,
    metadata: Optional[dict] = None,
) -> None:
    """Emit a workflow update event."""
    manager = get_connection_manager()
    
    await manager.broadcast_to_project(project_id, {
        "type": "workflow_update",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "workflow_id": workflow_id,
            "current_phase": phase,
            "status": status,
            "progress_percent": progress,
            **(metadata or {}),
        },
    })
