"""
Agent management routes.

Status and control operations for AURORA-DEV agents.
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter()


# Agent registry (simulated - would connect to actual registry)
AVAILABLE_AGENTS = {
    "maestro": {
        "name": "Maestro",
        "tier": "orchestration",
        "description": "Project coordinator and task scheduler",
        "model": "claude-sonnet-4-20250514",
    },
    "memory_coordinator": {
        "name": "Memory Coordinator",
        "tier": "orchestration",
        "description": "Context management and learning system",
        "model": "claude-haiku-4-20250514",
    },
    "architect": {
        "name": "Architect",
        "tier": "planning",
        "description": "System design and technical decisions",
        "model": "claude-sonnet-4-20250514",
    },
    "backend": {
        "name": "Backend Developer",
        "tier": "implementation",
        "description": "API logic and business rules",
        "model": "claude-sonnet-4-20250514",
    },
    "frontend": {
        "name": "Frontend Developer",
        "tier": "implementation",
        "description": "UI/UX and components",
        "model": "claude-sonnet-4-20250514",
    },
    "database": {
        "name": "Database Specialist",
        "tier": "implementation",
        "description": "Schema design and migrations",
        "model": "claude-sonnet-4-20250514",
    },
    "integration": {
        "name": "Integration Engineer",
        "tier": "implementation",
        "description": "API calls and webhooks",
        "model": "claude-sonnet-4-20250514",
    },
    "test_engineer": {
        "name": "Test Engineer",
        "tier": "quality",
        "description": "Unit, integration, E2E testing",
        "model": "claude-sonnet-4-20250514",
    },
    "security_auditor": {
        "name": "Security Auditor",
        "tier": "quality",
        "description": "OWASP, CVE scans, secrets",
        "model": "claude-sonnet-4-20250514",
    },
    "code_reviewer": {
        "name": "Code Reviewer",
        "tier": "quality",
        "description": "SOLID principles, quality metrics",
        "model": "claude-sonnet-4-20250514",
    },
    "validator": {
        "name": "Validator",
        "tier": "quality",
        "description": "Oracle checks and delta debugging",
        "model": "claude-haiku-4-20250514",
    },
    "devops": {
        "name": "DevOps Engineer",
        "tier": "devops",
        "description": "CI/CD pipelines, Docker, K8s",
        "model": "claude-sonnet-4-20250514",
    },
    "documentation": {
        "name": "Documentation Agent",
        "tier": "devops",
        "description": "API docs, architecture, runbooks",
        "model": "claude-haiku-4-20250514",
    },
    "monitoring": {
        "name": "Monitoring Agent",
        "tier": "devops",
        "description": "Logs, alerts, performance",
        "model": "claude-haiku-4-20250514",
    },
}

# Agent status tracking
_agent_status: dict[str, dict] = {}


# Models

class AgentResponse(BaseModel):
    """Agent information response."""
    
    id: str
    name: str
    tier: str
    description: str
    model: str
    status: str
    current_task: Optional[str]
    tasks_completed: int
    tasks_failed: int
    last_active: Optional[str]


class AgentListResponse(BaseModel):
    """List of agents response."""
    
    agents: list[AgentResponse]
    total: int


class AgentMetrics(BaseModel):
    """Agent performance metrics."""
    
    agent_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_duration_ms: float
    token_usage: dict[str, int]
    success_rate: float


# Helper functions

def _get_agent_status(agent_id: str) -> dict:
    """Get or create agent status."""
    if agent_id not in _agent_status:
        _agent_status[agent_id] = {
            "status": "idle",
            "current_task": None,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "last_active": None,
        }
    return _agent_status[agent_id]


# Routes

@router.get("", response_model=AgentListResponse)
async def list_agents(tier: Optional[str] = None):
    """
    List all available agents.
    
    Optionally filter by tier (orchestration, planning, implementation, quality, devops).
    """
    agents = []
    
    for agent_id, info in AVAILABLE_AGENTS.items():
        if tier and info["tier"] != tier:
            continue
        
        status = _get_agent_status(agent_id)
        
        agents.append(AgentResponse(
            id=agent_id,
            name=info["name"],
            tier=info["tier"],
            description=info["description"],
            model=info["model"],
            status=status["status"],
            current_task=status["current_task"],
            tasks_completed=status["tasks_completed"],
            tasks_failed=status["tasks_failed"],
            last_active=status["last_active"],
        ))
    
    return AgentListResponse(agents=agents, total=len(agents))


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get details for a specific agent."""
    if agent_id not in AVAILABLE_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    
    info = AVAILABLE_AGENTS[agent_id]
    status = _get_agent_status(agent_id)
    
    return AgentResponse(
        id=agent_id,
        name=info["name"],
        tier=info["tier"],
        description=info["description"],
        model=info["model"],
        status=status["status"],
        current_task=status["current_task"],
        tasks_completed=status["tasks_completed"],
        tasks_failed=status["tasks_failed"],
        last_active=status["last_active"],
    )


@router.get("/{agent_id}/metrics", response_model=AgentMetrics)
async def get_agent_metrics(agent_id: str):
    """Get performance metrics for an agent."""
    if agent_id not in AVAILABLE_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    
    status = _get_agent_status(agent_id)
    total = status["tasks_completed"] + status["tasks_failed"]
    
    return AgentMetrics(
        agent_id=agent_id,
        total_tasks=total,
        completed_tasks=status["tasks_completed"],
        failed_tasks=status["tasks_failed"],
        average_duration_ms=0.0,  # Would be calculated from actual data
        token_usage={"input": 0, "output": 0},
        success_rate=status["tasks_completed"] / total if total > 0 else 1.0,
    )


@router.post("/{agent_id}/reset")
async def reset_agent(agent_id: str):
    """Reset an agent's state."""
    if agent_id not in AVAILABLE_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    
    _agent_status[agent_id] = {
        "status": "idle",
        "current_task": None,
        "tasks_completed": 0,
        "tasks_failed": 0,
        "last_active": None,
    }
    
    logger.info(f"Reset agent: {agent_id}")
    
    return {"message": f"Agent reset: {agent_id}"}


@router.get("/tiers/summary")
async def get_tier_summary():
    """Get summary of agents by tier."""
    summary = {}
    
    for agent_id, info in AVAILABLE_AGENTS.items():
        tier = info["tier"]
        if tier not in summary:
            summary[tier] = {"count": 0, "agents": []}
        summary[tier]["count"] += 1
        summary[tier]["agents"].append(agent_id)
    
    return summary
