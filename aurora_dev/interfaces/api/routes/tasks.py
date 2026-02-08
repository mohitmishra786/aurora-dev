"""
Task management routes.

Operations for managing tasks within projects.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter()


# In-memory task storage (would use database in production)
_tasks: dict[str, dict] = {}


# Request/Response Models

class TaskCreateRequest(BaseModel):
    """Request to create a new task."""
    
    project_id: str
    task_type: str = Field(..., description="Type: feature, bugfix, refactor")
    description: str = Field(..., min_length=1)
    priority: int = Field(default=5, ge=1, le=10)
    assigned_agent: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    """Task response model."""
    
    id: str
    project_id: str
    task_type: str
    description: str
    status: str
    priority: int
    assigned_agent: Optional[str]
    progress_percent: int
    created_at: str
    updated_at: str


class TaskListResponse(BaseModel):
    """List of tasks response."""
    
    tasks: list[TaskResponse]
    total: int


class TaskUpdateRequest(BaseModel):
    """Request to update a task."""
    
    status: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=10)
    assigned_agent: Optional[str] = None
    progress_percent: Optional[int] = Field(default=None, ge=0, le=100)


# Routes

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(request: TaskCreateRequest):
    """Create a new task."""
    task_id = str(uuid4())[:8]
    now = datetime.now()
    
    task = {
        "id": task_id,
        "project_id": request.project_id,
        "task_type": request.task_type,
        "description": request.description,
        "status": "pending",
        "priority": request.priority,
        "assigned_agent": request.assigned_agent,
        "progress_percent": 0,
        "metadata": request.metadata,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    _tasks[task_id] = task
    logger.info(f"Created task: {task_id}")
    
    return TaskResponse(**{k: v for k, v in task.items() if k != "metadata"})


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    project_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
):
    """
    List tasks with optional filtering.
    
    Filter by project, status, or task type.
    """
    tasks = list(_tasks.values())
    
    if project_id:
        tasks = [t for t in tasks if t["project_id"] == project_id]
    
    if status_filter:
        tasks = [t for t in tasks if t["status"] == status_filter]
    
    if task_type:
        tasks = [t for t in tasks if t["task_type"] == task_type]
    
    # Sort by priority (higher first) then created_at
    tasks.sort(key=lambda t: (-t["priority"], t["created_at"]))
    
    # Paginate
    total = len(tasks)
    tasks = tasks[offset:offset + limit]
    
    responses = [
        TaskResponse(**{k: v for k, v in t.items() if k != "metadata"})
        for t in tasks
    ]
    
    return TaskListResponse(tasks=responses, total=total)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get a specific task by ID."""
    task = _tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    return TaskResponse(**{k: v for k, v in task.items() if k != "metadata"})


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, request: TaskUpdateRequest):
    """Update a task."""
    task = _tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    # Update fields
    if request.status is not None:
        task["status"] = request.status
    if request.priority is not None:
        task["priority"] = request.priority
    if request.assigned_agent is not None:
        task["assigned_agent"] = request.assigned_agent
    if request.progress_percent is not None:
        task["progress_percent"] = request.progress_percent
    
    task["updated_at"] = datetime.now().isoformat()
    
    logger.info(f"Updated task: {task_id}")
    
    return TaskResponse(**{k: v for k, v in task.items() if k != "metadata"})


@router.post("/{task_id}/start")
async def start_task(task_id: str):
    """Start executing a task."""
    task = _tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    if task["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Task not in pending state")
    
    task["status"] = "running"
    task["updated_at"] = datetime.now().isoformat()
    
    logger.info(f"Started task: {task_id}")
    
    return {"message": f"Task started: {task_id}", "status": "running"}


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a running or pending task."""
    task = _tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    if task["status"] in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Task already finished")
    
    task["status"] = "cancelled"
    task["updated_at"] = datetime.now().isoformat()
    
    logger.info(f"Cancelled task: {task_id}")
    
    return {"message": f"Task cancelled: {task_id}", "status": "cancelled"}


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a task."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    del _tasks[task_id]
    logger.info(f"Deleted task: {task_id}")
    
    return {"message": f"Task deleted: {task_id}"}
