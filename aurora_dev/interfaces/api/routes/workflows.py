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


# ============================================================================
# Human-in-the-Loop Endpoints
# ============================================================================


class ApprovalRequest(BaseModel):
    """Request to approve or reject a paused workflow."""
    
    approved: bool = Field(..., description="True to approve, False to reject")
    reviewer_id: str = Field(..., description="ID of the approving user")
    comments: Optional[str] = Field(None, description="Review comments")
    modifications: Optional[dict[str, Any]] = Field(None, description="Optional workflow data modifications")


class ApprovalResponse(BaseModel):
    """Response after processing approval."""
    
    workflow_id: str
    status: str
    message: str
    resumed_at: Optional[str] = None


class WorkflowGraphNode(BaseModel):
    """Node in the workflow execution graph."""
    
    id: str
    phase: str
    status: str  # pending, active, completed, failed, skipped
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class WorkflowGraphEdge(BaseModel):
    """Edge connecting workflow phases."""
    
    source: str
    target: str
    transition_type: str  # automatic, conditional, human_approval


class WorkflowGraphResponse(BaseModel):
    """DAG visualization of workflow execution status."""
    
    workflow_id: str
    nodes: list[WorkflowGraphNode]
    edges: list[WorkflowGraphEdge]
    current_phase: str
    pending_approval: bool
    checkpoint: Optional[str] = None


class PendingApprovalItem(BaseModel):
    """Item in the pending approvals list."""
    
    workflow_id: str
    project_id: str
    current_phase: str
    checkpoint: Optional[str]
    paused_at: str
    task_description: str


class PendingApprovalsResponse(BaseModel):
    """List of workflows awaiting approval."""
    
    pending: list[PendingApprovalItem]
    total: int


def _get_phase_status(workflow: dict, phase: str) -> str:
    """Determine the status of a phase in a workflow."""
    current = workflow["current_phase"]
    
    # Define phase order
    phase_order = [
        "initialization", "requirements", "design", "implementation",
        "testing", "code_review", "security_audit", "deployment", "completed"
    ]
    
    if phase == current:
        if workflow["status"] in ["paused", "awaiting_approval"]:
            return "paused"
        return "active"
    
    try:
        current_idx = phase_order.index(current)
        phase_idx = phase_order.index(phase)
        
        if phase_idx < current_idx:
            # Check phase results for actual status
            results = workflow.get("phase_results", {})
            if phase in results and results[phase].get("error"):
                return "failed"
            return "completed"
        return "pending"
    except ValueError:
        return "unknown"


def _build_workflow_graph(workflow: dict) -> tuple[list[WorkflowGraphNode], list[WorkflowGraphEdge]]:
    """Build a DAG representation of the workflow."""
    phases = [
        "requirements", "design", "implementation", "testing",
        "code_review", "security_audit", "deployment", "completed"
    ]
    
    nodes = []
    for phase in phases:
        status = _get_phase_status(workflow, phase)
        nodes.append(WorkflowGraphNode(
            id=phase,
            phase=phase,
            status=status,
            started_at=None,  # Would come from phase_results
            completed_at=None,
        ))
    
    # Standard edges
    edges = [
        WorkflowGraphEdge(source="requirements", target="design", transition_type="automatic"),
        WorkflowGraphEdge(source="design", target="implementation", transition_type="automatic"),
        WorkflowGraphEdge(source="implementation", target="testing", transition_type="automatic"),
        WorkflowGraphEdge(source="testing", target="code_review", transition_type="automatic"),
        WorkflowGraphEdge(source="code_review", target="security_audit", transition_type="automatic"),
        WorkflowGraphEdge(source="security_audit", target="deployment", transition_type="automatic"),
        WorkflowGraphEdge(source="deployment", target="completed", transition_type="automatic"),
        # Feedback loops
        WorkflowGraphEdge(source="testing", target="implementation", transition_type="conditional"),
        WorkflowGraphEdge(source="code_review", target="implementation", transition_type="conditional"),
    ]
    
    # Add human approval edges if in collaborative mode
    if workflow.get("metadata", {}).get("orchestrator_mode") == "collaborative":
        edges.append(WorkflowGraphEdge(source="design", target="awaiting_approval", transition_type="human_approval"))
        edges.append(WorkflowGraphEdge(source="security_audit", target="awaiting_approval", transition_type="human_approval"))
    
    return nodes, edges


@router.get("/{workflow_id}/graph", response_model=WorkflowGraphResponse)
async def get_workflow_graph(workflow_id: str):
    """
    Get DAG visualization of workflow execution status.
    
    Returns the workflow as a directed graph with nodes for each phase
    and edges showing possible transitions.
    """
    workflow = _workflows.get(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    nodes, edges = _build_workflow_graph(workflow)
    
    return WorkflowGraphResponse(
        workflow_id=workflow_id,
        nodes=nodes,
        edges=edges,
        current_phase=workflow["current_phase"],
        pending_approval=workflow["status"] in ["paused", "awaiting_approval"],
        checkpoint=workflow.get("metadata", {}).get("approval_checkpoint"),
    )


@router.post("/{workflow_id}/approval", response_model=ApprovalResponse)
async def submit_approval(workflow_id: str, request: ApprovalRequest):
    """
    Submit human approval for a paused workflow.
    
    If approved, the workflow resumes execution from where it paused.
    If rejected, the workflow is cancelled.
    """
    workflow = _workflows.get(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    if workflow["status"] not in ["paused", "awaiting_approval"]:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow is not awaiting approval. Current status: {workflow['status']}"
        )
    
    now = datetime.now()
    
    # Store approval decision
    approval_record = {
        "approved": request.approved,
        "reviewer_id": request.reviewer_id,
        "comments": request.comments,
        "decided_at": now.isoformat(),
    }
    
    if "approvals" not in workflow:
        workflow["approvals"] = []
    workflow["approvals"].append(approval_record)
    
    if request.approved:
        # Apply any modifications
        if request.modifications:
            workflow["metadata"].update(request.modifications)
        
        # Resume workflow
        workflow["status"] = "running"
        workflow["updated_at"] = now.isoformat()
        
        logger.info(f"Workflow {workflow_id} approved by {request.reviewer_id}")
        
        return ApprovalResponse(
            workflow_id=workflow_id,
            status="resumed",
            message=f"Workflow approved and resumed by {request.reviewer_id}",
            resumed_at=now.isoformat(),
        )
    else:
        # Reject and cancel workflow
        workflow["status"] = "cancelled"
        workflow["updated_at"] = now.isoformat()
        workflow["error"] = f"Rejected by {request.reviewer_id}: {request.comments or 'No reason provided'}"
        
        logger.info(f"Workflow {workflow_id} rejected by {request.reviewer_id}")
        
        return ApprovalResponse(
            workflow_id=workflow_id,
            status="rejected",
            message=f"Workflow rejected by {request.reviewer_id}",
        )


@router.get("/pending-approvals", response_model=PendingApprovalsResponse)
async def list_pending_approvals(project_id: Optional[str] = None):
    """
    List all workflows awaiting human approval.
    
    Optionally filter by project_id.
    """
    pending = []
    
    for wf in _workflows.values():
        if wf["status"] not in ["paused", "awaiting_approval"]:
            continue
        
        if project_id and wf["project_id"] != project_id:
            continue
        
        pending.append(PendingApprovalItem(
            workflow_id=wf["id"],
            project_id=wf["project_id"],
            current_phase=wf["current_phase"],
            checkpoint=wf.get("metadata", {}).get("approval_checkpoint"),
            paused_at=wf.get("metadata", {}).get("paused_at", wf["updated_at"]),
            task_description=wf.get("task_description", ""),
        ))
    
    # Sort by paused_at, oldest first
    pending.sort(key=lambda x: x.paused_at)
    
    return PendingApprovalsResponse(pending=pending, total=len(pending))


@router.post("/{workflow_id}/pause")
async def pause_workflow(workflow_id: str, reason: Optional[str] = None):
    """
    Manually pause a running workflow for human review.
    
    The workflow can be resumed via the approval endpoint.
    """
    workflow = _workflows.get(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    if workflow["status"] != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Can only pause running workflows. Current status: {workflow['status']}"
        )
    
    now = datetime.now()
    
    workflow["status"] = "paused"
    workflow["updated_at"] = now.isoformat()
    workflow["metadata"]["paused_at"] = now.isoformat()
    workflow["metadata"]["pause_reason"] = reason or "manual_pause"
    workflow["metadata"]["resume_phase"] = workflow["current_phase"]
    
    logger.info(f"Paused workflow: {workflow_id} ({reason or 'manual'})")
    
    return {
        "message": f"Workflow paused: {workflow_id}",
        "paused_at": now.isoformat(),
        "resume_phase": workflow["current_phase"],
    }


@router.post("/{workflow_id}/resume")
async def resume_workflow(workflow_id: str):
    """
    Resume a paused workflow without approval (admin override).
    
    Use the approval endpoint for normal human-in-the-loop flow.
    """
    workflow = _workflows.get(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    if workflow["status"] not in ["paused", "awaiting_approval"]:
        raise HTTPException(
            status_code=400,
            detail=f"Can only resume paused workflows. Current status: {workflow['status']}"
        )
    
    now = datetime.now()
    
    workflow["status"] = "running"
    workflow["updated_at"] = now.isoformat()
    
    logger.info(f"Resumed workflow (admin): {workflow_id}")
    
    return {
        "message": f"Workflow resumed: {workflow_id}",
        "resumed_at": now.isoformat(),
    }

