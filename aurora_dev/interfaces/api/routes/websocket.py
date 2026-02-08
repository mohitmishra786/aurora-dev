"""
WebSocket endpoint for real-time workflow updates.

Provides WebSocket connections for clients to receive
real-time workflow state changes and approval requests.
"""
import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections for workflow updates."""
    
    def __init__(self):
        # workflow_id -> list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}
        # All connections (for broadcast)
        self.all_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket, workflow_id: Optional[str] = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.all_connections.append(websocket)
        
        if workflow_id:
            if workflow_id not in self.active_connections:
                self.active_connections[workflow_id] = []
            self.active_connections[workflow_id].append(websocket)
        
        logger.info(f"WebSocket connected: workflow={workflow_id}")
    
    def disconnect(self, websocket: WebSocket, workflow_id: Optional[str] = None):
        """Remove a WebSocket connection."""
        if websocket in self.all_connections:
            self.all_connections.remove(websocket)
        
        if workflow_id and workflow_id in self.active_connections:
            if websocket in self.active_connections[workflow_id]:
                self.active_connections[workflow_id].remove(websocket)
            if not self.active_connections[workflow_id]:
                del self.active_connections[workflow_id]
        
        logger.info(f"WebSocket disconnected: workflow={workflow_id}")
    
    async def send_to_workflow(self, workflow_id: str, message: dict):
        """Send a message to all connections watching a workflow."""
        if workflow_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[workflow_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # Remove failed connections
            for conn in disconnected:
                self.disconnect(conn, workflow_id)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.all_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)


# Singleton connection manager
manager = ConnectionManager()


@router.websocket("/workflows/{workflow_id}")
async def workflow_websocket(websocket: WebSocket, workflow_id: str):
    """
    WebSocket endpoint for workflow-specific updates.
    
    Clients connect to receive real-time updates about:
    - State changes (phase transitions)
    - Approval requests
    - Task completions
    - Errors
    """
    await manager.connect(websocket, workflow_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "workflow_id": workflow_id,
            "data": {
                "message": "Connected to workflow updates",
                "timestamp": datetime.utcnow().isoformat(),
            },
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (ping/pong or commands)
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0  # 30-second heartbeat
                )
                
                # Handle client commands
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "workflow_id": workflow_id,
                        "data": {"timestamp": datetime.utcnow().isoformat()},
                    })
                
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "workflow_id": workflow_id,
                    "data": {"timestamp": datetime.utcnow().isoformat()},
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, workflow_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, workflow_id)


@router.websocket("/all")
async def all_workflows_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for all workflow updates.
    
    Broadcasts all workflow events to connected clients.
    """
    await manager.connect(websocket)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "data": {
                "message": "Connected to all workflow updates",
                "timestamp": datetime.utcnow().isoformat(),
            },
        })
        
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )
                
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "data": {"timestamp": datetime.utcnow().isoformat()},
                    })
                    
            except asyncio.TimeoutError:
                await websocket.send_json({
                    "type": "heartbeat",
                    "data": {"timestamp": datetime.utcnow().isoformat()},
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Helper functions for emitting events

async def emit_state_change(
    workflow_id: str,
    phase: str,
    previous_phase: str,
    agent: Optional[str] = None,
):
    """Emit a workflow state change event."""
    event = {
        "type": "state_change",
        "workflow_id": workflow_id,
        "data": {
            "phase": phase,
            "previous_phase": previous_phase,
            "agent": agent,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    
    await manager.send_to_workflow(workflow_id, event)
    await manager.broadcast(event)


async def emit_approval_required(
    workflow_id: str,
    approval_id: str,
    phase: str,
    agent: str,
    description: str,
):
    """Emit an approval required event."""
    event = {
        "type": "approval_required",
        "workflow_id": workflow_id,
        "data": {
            "approval_id": approval_id,
            "phase": phase,
            "agent": agent,
            "message": description,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    
    await manager.send_to_workflow(workflow_id, event)
    await manager.broadcast(event)


async def emit_task_complete(
    workflow_id: str,
    task_id: str,
    agent: str,
    success: bool,
):
    """Emit a task completion event."""
    event = {
        "type": "task_complete",
        "workflow_id": workflow_id,
        "data": {
            "task_id": task_id,
            "agent": agent,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    
    await manager.send_to_workflow(workflow_id, event)


async def emit_error(
    workflow_id: str,
    error_message: str,
    agent: Optional[str] = None,
):
    """Emit an error event."""
    event = {
        "type": "error",
        "workflow_id": workflow_id,
        "data": {
            "message": error_message,
            "agent": agent,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    
    await manager.send_to_workflow(workflow_id, event)
