"""
Workflow execution routes.

Operations for running and managing LangGraph workflows.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter()


# In-memory workflow tracking
_workflows: dict[str, dict] = {}


# Models

class WorkflowStartRequest(BaseModel):
    """Request to start a workflow."""
    
    project_id: str
    workflow_type: str = Field(..., description="Type: feature, bugfix, parallel_services")
    task_description: str
    max_attempts: int = Field(default=5, ge=1, le=10)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowResponse(BaseModel):
    """Workflow execution response."""
    
    id: str
    project_id: str
    workflow_type: str
    status: str
    current_phase: str
    attempt_number: int
    max_attempts: int
    progress_percent: int
    started_at: str
    updated_at: str
    completed_at: Optional[str]
    error: Optional[str]


class WorkflowListResponse(BaseModel):
    """List of workflows response."""
    
    workflows: list[WorkflowResponse]
    total: int


class WorkflowPhaseResult(BaseModel):
    """Result from a workflow phase."""
    
    phase: str
    status: str
    agent: str
    duration_ms: float
    output: Optional[str]
    error: Optional[str]


# Routes

@router.post("", response_model=WorkflowResponse)
async def start_workflow(
    request: WorkflowStartRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start a new workflow execution.
    
    The workflow runs asynchronously in the background.
    Use the status endpoint to monitor progress.
    """
    workflow_id = str(uuid4())[:12]
    now = datetime.now()
    
    workflow = {
        "id": workflow_id,
        "project_id": request.project_id,
        "workflow_type": request.workflow_type,
        "task_description": request.task_description,
        "status": "starting",
        "current_phase": "initialization",
        "attempt_number": 1,
        "max_attempts": request.max_attempts,
        "progress_percent": 0,
        "phase_results": {},
        "reflections": [],
        "metadata": request.metadata,
        "started_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "completed_at": None,
        "error": None,
    }
    
    _workflows[workflow_id] = workflow
    
    # Would start actual workflow execution here
    # background_tasks.add_task(execute_workflow, workflow_id)
    
    # Simulate workflow start
    workflow["status"] = "running"
    
    logger.info(f"Started workflow: {workflow_id} ({request.workflow_type})")
    
    return WorkflowResponse(
        id=workflow["id"],
        project_id=workflow["project_id"],
        workflow_type=workflow["workflow_type"],
        status=workflow["status"],
        current_phase=workflow["current_phase"],
        attempt_number=workflow["attempt_number"],
        max_attempts=workflow["max_attempts"],
        progress_percent=workflow["progress_percent"],
        started_at=workflow["started_at"],
        updated_at=workflow["updated_at"],
        completed_at=workflow["completed_at"],
        error=workflow["error"],
    )


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    project_id: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    """List all workflows with optional filtering."""
    workflows = list(_workflows.values())
    
    if project_id:
        workflows = [w for w in workflows if w["project_id"] == project_id]
    
    if status_filter:
        workflows = [w for w in workflows if w["status"] == status_filter]
    
    # Sort by started_at descending
    workflows.sort(key=lambda w: w["started_at"], reverse=True)
    
    responses = [
        WorkflowResponse(
            id=w["id"],
            project_id=w["project_id"],
            workflow_type=w["workflow_type"],
            status=w["status"],
            current_phase=w["current_phase"],
            attempt_number=w["attempt_number"],
            max_attempts=w["max_attempts"],
            progress_percent=w["progress_percent"],
            started_at=w["started_at"],
            updated_at=w["updated_at"],
            completed_at=w["completed_at"],
            error=w["error"],
        )
        for w in workflows
    ]
    
    return WorkflowListResponse(workflows=responses, total=len(responses))


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """Get details for a specific workflow."""
    workflow = _workflows.get(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    return WorkflowResponse(
        id=workflow["id"],
        project_id=workflow["project_id"],
        workflow_type=workflow["workflow_type"],
        status=workflow["status"],
        current_phase=workflow["current_phase"],
        attempt_number=workflow["attempt_number"],
        max_attempts=workflow["max_attempts"],
        progress_percent=workflow["progress_percent"],
        started_at=workflow["started_at"],
        updated_at=workflow["updated_at"],
        completed_at=workflow["completed_at"],
        error=workflow["error"],
    )


@router.get("/{workflow_id}/phases")
async def get_workflow_phases(workflow_id: str):
    """Get phase results for a workflow."""
    workflow = _workflows.get(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    return {
        "workflow_id": workflow_id,
        "phases": workflow.get("phase_results", {}),
    }


@router.get("/{workflow_id}/reflections")
async def get_workflow_reflections(workflow_id: str):
    """Get reflections generated during workflow execution."""
    workflow = _workflows.get(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    return {
        "workflow_id": workflow_id,
        "reflections": workflow.get("reflections", []),
        "attempt_number": workflow["attempt_number"],
    }


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str):
    """Cancel a running workflow."""
    workflow = _workflows.get(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    if workflow["status"] in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Workflow already finished")
    
    workflow["status"] = "cancelled"
    workflow["updated_at"] = datetime.now().isoformat()
    
    logger.info(f"Cancelled workflow: {workflow_id}")
    
    return {"message": f"Workflow cancelled: {workflow_id}"}


@router.post("/{workflow_id}/retry")
async def retry_workflow(workflow_id: str):
    """Retry a failed workflow from the last failed phase."""
    workflow = _workflows.get(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    if workflow["status"] != "failed":
        raise HTTPException(status_code=400, detail="Can only retry failed workflows")
    
    if workflow["attempt_number"] >= workflow["max_attempts"]:
        raise HTTPException(status_code=400, detail="Max retry attempts reached")
    
    workflow["status"] = "running"
    workflow["attempt_number"] += 1
    workflow["updated_at"] = datetime.now().isoformat()
    
    logger.info(f"Retrying workflow: {workflow_id} (attempt {workflow['attempt_number']})")
    
    return {
        "message": f"Workflow retry started: {workflow_id}",
        "attempt_number": workflow["attempt_number"],
    }


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow record."""
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    del _workflows[workflow_id]
    logger.info(f"Deleted workflow: {workflow_id}")
    
    return {"message": f"Workflow deleted: {workflow_id}"}
