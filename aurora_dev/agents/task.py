"""
Task Definition System for AURORA-DEV.

This module provides Pydantic models for defining tasks, managing
dependencies, and tracking task execution. Tasks are the fundamental
units of work assigned to agents.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskPriority(Enum):
    """Task priority levels."""
    
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class TaskStatus(Enum):
    """Task execution status."""
    
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    WAITING_DEPENDENCY = "waiting_dependency"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskType(Enum):
    """Types of tasks in the system."""
    
    # Planning & Analysis
    ANALYZE_REQUIREMENTS = "analyze_requirements"
    DESIGN_ARCHITECTURE = "design_architecture"
    CREATE_PLAN = "create_plan"
    RESEARCH = "research"
    
    # Implementation
    IMPLEMENT_FEATURE = "implement_feature"
    WRITE_CODE = "write_code"
    REFACTOR = "refactor"
    FIX_BUG = "fix_bug"
    
    # Testing
    WRITE_TESTS = "write_tests"
    RUN_TESTS = "run_tests"
    INTEGRATION_TEST = "integration_test"
    PERFORMANCE_TEST = "performance_test"
    
    # Quality
    CODE_REVIEW = "code_review"
    SECURITY_AUDIT = "security_audit"
    VALIDATE = "validate"
    
    # DevOps
    DEPLOY = "deploy"
    CONFIGURE = "configure"
    MONITOR = "monitor"
    DOCUMENT = "document"
    
    # Meta
    ORCHESTRATE = "orchestrate"
    COORDINATE = "coordinate"
    HANDOFF = "handoff"


class TaskComplexity(Enum):
    """Task complexity ratings (1-10 scale)."""
    
    TRIVIAL = 1        # Trivial, no analysis needed
    VERY_LOW = 2       # Minimal changes, well-defined
    LOW = 3            # Straightforward with minor decisions
    LOW_MEDIUM = 4     # Some planning, limited scope
    MEDIUM = 5         # Requires analysis and planning
    MEDIUM_HIGH = 6    # Multiple components, cross-cutting
    HIGH = 7           # Complex, significant design decisions
    VERY_HIGH = 8      # Highly complex, multiple subsystems
    CRITICAL = 9       # Architectural changes, high risk
    EXTREME = 10       # System-wide refactor, maximum uncertainty



class TaskResult(BaseModel):
    """Result of task execution."""
    
    success: bool = Field(..., description="Whether task completed successfully")
    output: Any = Field(default=None, description="Task output data")
    artifacts: list[str] = Field(
        default_factory=list,
        description="List of artifact paths created",
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metrics",
    )
    
    model_config = ConfigDict(frozen=True)


class TaskDefinition(BaseModel):
    """
    Complete task definition for agent execution.
    
    Defines the task requirements, dependencies, constraints,
    and execution parameters.
    """
    
    # Identity
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique task identifier",
    )
    name: str = Field(..., description="Human-readable task name")
    description: str = Field(..., description="Detailed task description")
    type: TaskType = Field(..., description="Type of task")
    
    # Priority & Complexity
    priority: TaskPriority = Field(
        default=TaskPriority.NORMAL,
        description="Task priority level",
    )
    complexity: TaskComplexity = Field(
        default=TaskComplexity.MEDIUM,
        description="Task complexity rating",
    )
    
    # Assignment
    assigned_agent_id: Optional[str] = Field(
        default=None,
        description="ID of assigned agent",
    )
    target_agent_role: Optional[str] = Field(
        default=None,
        description="Target agent role for assignment",
    )
    
    # Dependencies
    dependencies: list[str] = Field(
        default_factory=list,
        description="IDs of tasks this task depends on",
    )
    parent_task_id: Optional[str] = Field(
        default=None,
        description="Parent task ID for subtasks",
    )
    
    # Context
    project_id: Optional[str] = Field(
        default=None,
        description="Associated project ID",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Task context and input data",
    )
    requirements: list[str] = Field(
        default_factory=list,
        description="Specific requirements for completion",
    )
    
    # Execution Parameters
    timeout_seconds: int = Field(
        default=300,
        ge=1,
        le=7200,
        description="Execution timeout in seconds",
    )
    max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum execution attempts",
    )
    
    # Estimation
    estimated_tokens: int = Field(
        default=1000,
        ge=0,
        description="Estimated tokens for completion",
    )
    estimated_duration_seconds: int = Field(
        default=60,
        ge=0,
        description="Estimated duration in seconds",
    )
    
    # Status Tracking
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current task status",
    )
    attempt_count: int = Field(
        default=0,
        ge=0,
        description="Number of execution attempts",
    )
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Task creation timestamp",
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Execution start timestamp",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Completion timestamp",
    )
    
    # Results
    result: Optional[TaskResult] = Field(
        default=None,
        description="Task execution result",
    )
    
    # Metadata
    tags: list[str] = Field(
        default_factory=list,
        description="Task tags for categorization",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )
    
    @field_validator("dependencies")
    @classmethod
    def validate_no_self_dependency(cls, v: list[str], info) -> list[str]:
        """Ensure task doesn't depend on itself."""
        task_id = info.data.get("id")
        if task_id and task_id in v:
            raise ValueError("Task cannot depend on itself")
        return v
    
    def is_ready(self, completed_tasks: set[str]) -> bool:
        """
        Check if task is ready to execute.
        
        Args:
            completed_tasks: Set of completed task IDs.
            
        Returns:
            True if all dependencies are satisfied.
        """
        return all(dep in completed_tasks for dep in self.dependencies)
    
    def mark_started(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.attempt_count += 1
    
    def mark_completed(self, result: TaskResult) -> None:
        """Mark task as completed with result."""
        self.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.result = result
    
    def mark_failed(self, error: str) -> None:
        """Mark task as failed with error."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.result = TaskResult(success=False, error=error)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get actual execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return (
            self.status == TaskStatus.FAILED
            and self.attempt_count < self.max_attempts
        )
    
    def to_agent_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary suitable for agent execution.
        
        Returns:
            Dictionary with task details for agent consumption.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "priority": self.priority.value,
            "complexity": self.complexity.value,
            "context": self.context,
            "requirements": self.requirements,
            "timeout_seconds": self.timeout_seconds,
            "attempt_number": self.attempt_count + 1,
            "max_attempts": self.max_attempts,
        }
    
    model_config = ConfigDict(use_enum_values=False, validate_assignment=True)


class TaskDependencyGraph:
    """
    Manages task dependencies as a directed acyclic graph.
    
    Provides topological sorting and dependency resolution.
    """
    
    def __init__(self) -> None:
        """Initialize the dependency graph."""
        self._tasks: dict[str, TaskDefinition] = {}
        self._edges: dict[str, set[str]] = {}  # task_id -> dependent task IDs
    
    def add_task(self, task: TaskDefinition) -> None:
        """
        Add a task to the graph.
        
        Args:
            task: The task to add.
            
        Raises:
            ValueError: If adding would create a cycle.
        """
        self._tasks[task.id] = task
        self._edges.setdefault(task.id, set())
        
        # Add edges from dependencies to this task
        for dep_id in task.dependencies:
            self._edges.setdefault(dep_id, set())
            self._edges[dep_id].add(task.id)
        
        # Validate no cycles
        if self._has_cycle():
            del self._tasks[task.id]
            for dep_id in task.dependencies:
                self._edges[dep_id].discard(task.id)
            raise ValueError(f"Adding task {task.id} would create a cycle")
    
    def remove_task(self, task_id: str) -> Optional[TaskDefinition]:
        """
        Remove a task from the graph.
        
        Args:
            task_id: The task ID to remove.
            
        Returns:
            The removed task, or None if not found.
        """
        task = self._tasks.pop(task_id, None)
        if task:
            # Remove edges
            self._edges.pop(task_id, None)
            for edges in self._edges.values():
                edges.discard(task_id)
            
            # Update dependents
            for dep_id in task.dependencies:
                if dep_id in self._edges:
                    self._edges[dep_id].discard(task_id)
        
        return task
    
    def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    def get_ready_tasks(self, completed: Optional[set[str]] = None) -> list[TaskDefinition]:
        """
        Get all tasks ready for execution.
        
        Args:
            completed: Set of completed task IDs.
            
        Returns:
            List of tasks with satisfied dependencies.
        """
        completed = completed or set()
        ready = []
        
        for task in self._tasks.values():
            if task.status in (TaskStatus.PENDING, TaskStatus.QUEUED):
                if task.is_ready(completed):
                    ready.append(task)
        
        # Sort by priority (higher first)
        ready.sort(key=lambda t: t.priority.value, reverse=True)
        return ready
    
    def get_dependent_tasks(self, task_id: str) -> list[TaskDefinition]:
        """Get tasks that depend on the given task."""
        dependent_ids = self._edges.get(task_id, set())
        return [self._tasks[tid] for tid in dependent_ids if tid in self._tasks]
    
    def topological_sort(self) -> list[TaskDefinition]:
        """
        Get tasks in topological order.
        
        Returns:
            List of tasks in dependency order.
        """
        in_degree: dict[str, int] = {tid: 0 for tid in self._tasks}
        
        for task in self._tasks.values():
            for dep_id in task.dependencies:
                if dep_id in self._tasks:
                    in_degree[task.id] += 1
        
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        result = []
        
        while queue:
            # Sort by priority within same dependency level
            queue.sort(key=lambda tid: self._tasks[tid].priority.value, reverse=True)
            task_id = queue.pop(0)
            result.append(self._tasks[task_id])
            
            for dep_id in self._edges.get(task_id, set()):
                if dep_id in in_degree:
                    in_degree[dep_id] -= 1
                    if in_degree[dep_id] == 0:
                        queue.append(dep_id)
        
        return result
    
    def _has_cycle(self) -> bool:
        """Check if graph has a cycle using DFS."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {tid: WHITE for tid in self._tasks}
        
        def dfs(task_id: str) -> bool:
            color[task_id] = GRAY
            for neighbor in self._edges.get(task_id, set()):
                if neighbor not in color:
                    continue
                if color[neighbor] == GRAY:
                    return True
                if color[neighbor] == WHITE and dfs(neighbor):
                    return True
            color[task_id] = BLACK
            return False
        
        return any(dfs(tid) for tid in self._tasks if color[tid] == WHITE)
    
    @property
    def task_count(self) -> int:
        """Get number of tasks in graph."""
        return len(self._tasks)
    
    def get_all_tasks(self) -> list[TaskDefinition]:
        """Get all tasks in the graph."""
        return list(self._tasks.values())
