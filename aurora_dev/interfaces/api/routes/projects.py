"""
Project management routes.

CRUD operations for managing AURORA-DEV projects.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from aurora_dev.core.project_manager import (
    ProjectManager,
    ProjectConfig,
    ProjectStatus,
    get_project_manager,
)
from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter()


# Request/Response Models

class ProjectConfigRequest(BaseModel):
    """Project configuration request."""
    
    language: str = "python"
    framework: Optional[str] = None
    database: Optional[str] = None
    deployment: Optional[str] = None
    custom_settings: dict[str, Any] = Field(default_factory=dict)


class ProjectCreateRequest(BaseModel):
    """Request to create a new project."""
    
    name: str = Field(..., min_length=1, max_length=100)
    path: str = Field(..., min_length=1)
    config: Optional[ProjectConfigRequest] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectResponse(BaseModel):
    """Project response model."""
    
    id: str
    name: str
    path: str
    status: str
    config: dict[str, Any]
    cost_summary: dict[str, Any]
    created_at: str
    updated_at: str


class ProjectListResponse(BaseModel):
    """List of projects response."""
    
    projects: list[ProjectResponse]
    total: int


# Routes

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(request: ProjectCreateRequest):
    """
    Create a new project.
    
    Creates a project with optional configuration. If no config
    is provided, the system will auto-detect from the project path.
    """
    manager = get_project_manager()
    
    try:
        config = None
        if request.config:
            config = ProjectConfig(
                language=request.config.language,
                framework=request.config.framework,
                database=request.config.database,
                deployment=request.config.deployment,
                custom_settings=request.config.custom_settings,
            )
        
        project = await manager.create(
            name=request.name,
            path=request.path,
            config=config,
            metadata=request.metadata,
        )
        
        logger.info(f"Created project: {project.id}")
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            path=str(project.path),
            status=project.status.value,
            config=project.config.to_dict(),
            cost_summary=manager.get_cost_summary(project.id),
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    status_filter: Optional[str] = None,
    active_only: bool = False,
):
    """
    List all projects.
    
    Optionally filter by status or show only active projects.
    """
    manager = get_project_manager()
    
    if active_only:
        projects = manager.list_active()
    else:
        projects = manager.list_projects()
    
    # Filter by status if specified
    if status_filter:
        try:
            target_status = ProjectStatus(status_filter)
            projects = [p for p in projects if p.status == target_status]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")
    
    responses = [
        ProjectResponse(
            id=p.id,
            name=p.name,
            path=str(p.path),
            status=p.status.value,
            config=p.config.to_dict(),
            cost_summary=manager.get_cost_summary(p.id),
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        )
        for p in projects
    ]
    
    return ProjectListResponse(projects=responses, total=len(responses))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get a specific project by ID."""
    manager = get_project_manager()
    
    projects = manager.list_projects()
    project = next((p for p in projects if p.id == project_id), None)
    
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        path=str(project.path),
        status=project.status.value,
        config=project.config.to_dict(),
        cost_summary=manager.get_cost_summary(project.id),
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.post("/{project_id}/switch")
async def switch_project(project_id: str):
    """Switch to a different project (make it active)."""
    manager = get_project_manager()
    
    try:
        context = await manager.switch(project_id)
        logger.info(f"Switched to project: {project_id}")
        
        return {
            "message": f"Switched to project: {project_id}",
            "context": {
                "project_id": context.project_id,
                "project_name": context.project_name,
                "memory_prefix": context.memory_prefix,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/archive")
async def archive_project(project_id: str):
    """Archive a project."""
    manager = get_project_manager()
    
    try:
        await manager.archive(project_id)
        logger.info(f"Archived project: {project_id}")
        return {"message": f"Project archived: {project_id}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """
    Delete a project from the manager.
    
    Note: This does not delete files on disk.
    """
    manager = get_project_manager()
    
    try:
        await manager.delete(project_id)
        logger.info(f"Deleted project: {project_id}")
        return {"message": f"Project deleted: {project_id}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{project_id}/costs")
async def get_project_costs(project_id: str):
    """Get detailed cost information for a project."""
    manager = get_project_manager()
    
    summary = manager.get_cost_summary(project_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    
    return {
        "project_id": project_id,
        **summary,
    }
