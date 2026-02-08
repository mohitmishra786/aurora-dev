"""
Main Orchestration Engine for AURORA-DEV.

Provides the central orchestration loop that coordinates agent
execution, manages workflows, and monitors project progress.
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4

from aurora_dev.core.config import get_settings
from aurora_dev.core.task_queue import TaskManager
from aurora_dev.core.task_queue.models import TaskPriority, TaskStatus


logger = logging.getLogger(__name__)


class ProjectPhase(Enum):
    """Project execution phases.
    
    Represents the high-level phases of project execution.
    """
    
    INITIALIZATION = "initialization"
    PLANNING = "planning"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"
    FAILED = "failed"


class OrchestrationMode(Enum):
    """Orchestration execution modes.
    
    Different modes for running the orchestration engine.
    """
    
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"


@dataclass
class ProjectContext:
    """Context for project execution.
    
    Attributes:
        project_id: Unique project identifier.
        name: Project name.
        description: Project description.
        goal: High-level project goal.
        tech_stack: Technology stack specification.
        phase: Current project phase.
        mode: Orchestration mode.
        created_at: Project creation timestamp.
        started_at: Optional execution start timestamp.
        completed_at: Optional completion timestamp.
        metadata: Additional project metadata.
    """
    
    project_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    goal: str = ""
    tech_stack: list[str] = field(default_factory=list)
    phase: ProjectPhase = ProjectPhase.INITIALIZATION
    mode: OrchestrationMode = OrchestrationMode.HYBRID
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        """Check if project is actively running.
        
        Returns:
            True if project is in an active phase.
        """
        return self.phase not in {ProjectPhase.COMPLETED, ProjectPhase.FAILED}
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate project duration.
        
        Returns:
            Duration in seconds if started.
        """
        if self.started_at is None:
            return None
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "goal": self.goal,
            "tech_stack": self.tech_stack,
            "phase": self.phase.value,
            "mode": self.mode.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }


@dataclass
class OrchestrationResult:
    """Result from orchestration execution.
    
    Attributes:
        project_id: Project identifier.
        phase: Final project phase.
        success: Whether execution was successful.
        tasks_completed: Number of tasks completed.
        tasks_failed: Number of tasks failed.
        duration_seconds: Total execution duration.
        outputs: Task outputs by task ID.
        errors: Any errors encountered.
    """
    
    project_id: str
    phase: ProjectPhase
    success: bool
    tasks_completed: int = 0
    tasks_failed: int = 0
    duration_seconds: float = 0.0
    outputs: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "project_id": self.project_id,
            "phase": self.phase.value,
            "success": self.success,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "duration_seconds": self.duration_seconds,
            "outputs": self.outputs,
            "errors": self.errors,
        }


class OrchestrationEngine:
    """Main orchestration engine for AURORA-DEV.
    
    Coordinates agent execution, manages workflows, and monitors
    project progress through all phases.
    
    Attributes:
        task_manager: Task queue manager.
        projects: Active project contexts.
        callbacks: Phase transition callbacks.
    """
    
    def __init__(self) -> None:
        """Initialize the orchestration engine."""
        self.task_manager = TaskManager()
        self.projects: dict[str, ProjectContext] = {}
        self.callbacks: dict[ProjectPhase, list[Callable]] = {}
        self._settings = get_settings()
        
        logger.info("OrchestrationEngine initialized")
    
    def create_project(
        self,
        name: str,
        goal: str,
        description: str = "",
        tech_stack: Optional[list[str]] = None,
        mode: OrchestrationMode = OrchestrationMode.HYBRID,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ProjectContext:
        """Create a new project for orchestration.
        
        Args:
            name: Project name.
            goal: High-level project goal.
            description: Project description.
            tech_stack: Technology stack.
            mode: Orchestration mode.
            metadata: Additional metadata.
            
        Returns:
            Created project context.
        """
        context = ProjectContext(
            name=name,
            description=description,
            goal=goal,
            tech_stack=tech_stack or [],
            mode=mode,
            metadata=metadata or {},
        )
        
        self.projects[context.project_id] = context
        logger.info(f"Created project: {context.project_id} - {name}")
        
        return context
    
    async def start_project(
        self,
        project_id: str,
    ) -> OrchestrationResult:
        """Start project execution.
        
        Args:
            project_id: Project identifier.
            
        Returns:
            Orchestration result.
            
        Raises:
            ValueError: If project not found.
        """
        context = self.projects.get(project_id)
        if context is None:
            raise ValueError(f"Project not found: {project_id}")
        
        context.started_at = datetime.now(timezone.utc)
        logger.info(f"Starting project: {project_id}")
        
        try:
            result = await self._execute_workflow(context)
            return result
        except Exception as e:
            logger.error(f"Project {project_id} failed: {e}")
            context.phase = ProjectPhase.FAILED
            return OrchestrationResult(
                project_id=project_id,
                phase=ProjectPhase.FAILED,
                success=False,
                errors=[str(e)],
            )
    
    async def _execute_workflow(
        self,
        context: ProjectContext,
    ) -> OrchestrationResult:
        """Execute the main workflow for a project.
        
        Args:
            context: Project context.
            
        Returns:
            Orchestration result.
        """
        tasks_completed = 0
        tasks_failed = 0
        outputs: dict[str, Any] = {}
        errors: list[str] = []
        
        try:
            await self._transition_phase(context, ProjectPhase.PLANNING)
            planning_result = await self._execute_planning_phase(context)
            outputs["planning"] = planning_result
            tasks_completed += 1
            
            await self._transition_phase(context, ProjectPhase.DESIGN)
            design_result = await self._execute_design_phase(context, planning_result)
            outputs["design"] = design_result
            tasks_completed += 1
            
            await self._transition_phase(context, ProjectPhase.IMPLEMENTATION)
            impl_result = await self._execute_implementation_phase(context, design_result)
            outputs["implementation"] = impl_result
            tasks_completed += impl_result.get("tasks_count", 1)
            tasks_failed += impl_result.get("failures", 0)
            
            await self._transition_phase(context, ProjectPhase.TESTING)
            test_result = await self._execute_testing_phase(context, impl_result)
            outputs["testing"] = test_result
            tasks_completed += 1
            
            await self._transition_phase(context, ProjectPhase.REVIEW)
            review_result = await self._execute_review_phase(context, impl_result)
            outputs["review"] = review_result
            tasks_completed += 1
            
            await self._transition_phase(context, ProjectPhase.DEPLOYMENT)
            deploy_result = await self._execute_deployment_phase(context)
            outputs["deployment"] = deploy_result
            tasks_completed += 1
            
            await self._transition_phase(context, ProjectPhase.COMPLETED)
            context.completed_at = datetime.now(timezone.utc)
            
            return OrchestrationResult(
                project_id=context.project_id,
                phase=ProjectPhase.COMPLETED,
                success=True,
                tasks_completed=tasks_completed,
                tasks_failed=tasks_failed,
                duration_seconds=context.duration_seconds or 0.0,
                outputs=outputs,
            )
            
        except Exception as e:
            errors.append(str(e))
            logger.error(f"Workflow execution failed: {e}")
            
            return OrchestrationResult(
                project_id=context.project_id,
                phase=context.phase,
                success=False,
                tasks_completed=tasks_completed,
                tasks_failed=tasks_failed + 1,
                duration_seconds=context.duration_seconds or 0.0,
                outputs=outputs,
                errors=errors,
            )
    
    async def _transition_phase(
        self,
        context: ProjectContext,
        new_phase: ProjectPhase,
    ) -> None:
        """Transition to a new project phase.
        
        Args:
            context: Project context.
            new_phase: Target phase.
        """
        old_phase = context.phase
        context.phase = new_phase
        
        logger.info(f"Project {context.project_id}: {old_phase.value} -> {new_phase.value}")
        
        callbacks = self.callbacks.get(new_phase, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(context)
                else:
                    callback(context)
            except Exception as e:
                logger.error(f"Phase callback error: {e}")
    
    async def _execute_planning_phase(
        self,
        context: ProjectContext,
    ) -> dict[str, Any]:
        """Execute the planning phase.
        
        Args:
            context: Project context.
            
        Returns:
            Planning results.
        """
        from aurora_dev.agents.specialized.maestro import MaestroAgent
        
        maestro = MaestroAgent(project_id=context.project_id)
        
        tasks = await asyncio.to_thread(
            maestro.decompose_goal,
            context.goal,
            {"tech_stack": context.tech_stack, "description": context.description},
        )
        
        logger.info(f"Planning complete: {len(tasks)} tasks created")
        
        return {
            "tasks": [t.to_dict() if hasattr(t, "to_dict") else t for t in tasks],
            "task_count": len(tasks),
        }
    
    async def _execute_design_phase(
        self,
        context: ProjectContext,
        planning_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the design phase.
        
        Args:
            context: Project context.
            planning_result: Results from planning phase.
            
        Returns:
            Design results.
        """
        from aurora_dev.agents.specialized.architect import ArchitectAgent
        
        architect = ArchitectAgent(project_id=context.project_id)
        
        response = await asyncio.to_thread(
            architect.execute,
            {
                "operation": "design_system",
                "goal": context.goal,
                "tech_stack": context.tech_stack,
                "tasks": planning_result.get("tasks", []),
            },
        )
        
        logger.info("Design phase complete")
        
        return {
            "architecture": response.content if hasattr(response, "content") else str(response),
            "success": response.success if hasattr(response, "success") else True,
        }
    
    async def _execute_implementation_phase(
        self,
        context: ProjectContext,
        design_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the implementation phase.
        
        Args:
            context: Project context.
            design_result: Results from design phase.
            
        Returns:
            Implementation results.
        """
        task_ids: list[str] = []
        
        if context.mode == OrchestrationMode.PARALLEL:
            task_ids = await self._execute_parallel_implementation(context)
        else:
            task_ids = await self._execute_sequential_implementation(context)
        
        completed = 0
        failed = 0
        
        for task_id in task_ids:
            result = self.task_manager.get_result(task_id)
            if result:
                if result.success:
                    completed += 1
                else:
                    failed += 1
        
        logger.info(f"Implementation complete: {completed} succeeded, {failed} failed")
        
        return {
            "task_ids": task_ids,
            "tasks_count": len(task_ids),
            "completed": completed,
            "failures": failed,
        }
    
    async def _execute_parallel_implementation(
        self,
        context: ProjectContext,
    ) -> list[str]:
        """Execute implementation tasks in parallel.
        
        Args:
            context: Project context.
            
        Returns:
            List of task IDs.
        """
        task_ids: list[str] = []
        
        backend_task = self.task_manager.submit(
            operation="implement_service",
            parameters={"service_name": "Core", "methods": ["create", "read", "update", "delete"]},
            priority=TaskPriority.HIGH,
            project_id=context.project_id,
        )
        task_ids.append(backend_task)
        
        return task_ids
    
    async def _execute_sequential_implementation(
        self,
        context: ProjectContext,
    ) -> list[str]:
        """Execute implementation tasks sequentially.
        
        Args:
            context: Project context.
            
        Returns:
            List of task IDs.
        """
        task_ids: list[str] = []
        
        task_id = self.task_manager.submit(
            operation="implement_endpoint",
            parameters={"endpoint": "/api/health", "method": "GET"},
            priority=TaskPriority.MEDIUM,
            project_id=context.project_id,
        )
        task_ids.append(task_id)
        
        return task_ids
    
    async def _execute_testing_phase(
        self,
        context: ProjectContext,
        impl_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the testing phase.
        
        Args:
            context: Project context.
            impl_result: Results from implementation phase.
            
        Returns:
            Testing results.
        """
        task_id = self.task_manager.submit(
            operation="generate_tests",
            parameters={"code": "", "coverage_target": 0.75},
            priority=TaskPriority.HIGH,
            project_id=context.project_id,
        )
        
        logger.info("Testing phase complete")
        
        return {
            "test_task_id": task_id,
            "coverage_target": 0.75,
        }
    
    async def _execute_review_phase(
        self,
        context: ProjectContext,
        impl_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the review phase.
        
        Args:
            context: Project context.
            impl_result: Results from implementation phase.
            
        Returns:
            Review results.
        """
        task_id = self.task_manager.submit(
            operation="code_review",
            parameters={"code": ""},
            priority=TaskPriority.MEDIUM,
            project_id=context.project_id,
        )
        
        logger.info("Review phase complete")
        
        return {
            "review_task_id": task_id,
        }
    
    async def _execute_deployment_phase(
        self,
        context: ProjectContext,
    ) -> dict[str, Any]:
        """Execute the deployment phase.
        
        Args:
            context: Project context.
            
        Returns:
            Deployment results.
        """
        logger.info("Deployment phase complete (simulated)")
        
        return {
            "environment": "staging",
            "status": "deployed",
        }
    
    def register_callback(
        self,
        phase: ProjectPhase,
        callback: Callable,
    ) -> None:
        """Register a callback for phase transitions.
        
        Args:
            phase: Phase to register callback for.
            callback: Callback function.
        """
        if phase not in self.callbacks:
            self.callbacks[phase] = []
        self.callbacks[phase].append(callback)
        logger.debug(f"Registered callback for phase: {phase.value}")
    
    def get_project_status(
        self,
        project_id: str,
    ) -> Optional[dict[str, Any]]:
        """Get status of a project.
        
        Args:
            project_id: Project identifier.
            
        Returns:
            Project status dictionary or None.
        """
        context = self.projects.get(project_id)
        if context is None:
            return None
        
        return {
            "project_id": project_id,
            "name": context.name,
            "phase": context.phase.value,
            "is_active": context.is_active,
            "duration_seconds": context.duration_seconds,
            "created_at": context.created_at.isoformat(),
        }
    
    def list_projects(self) -> list[dict[str, Any]]:
        """List all projects.
        
        Returns:
            List of project status dictionaries.
        """
        return [
            self.get_project_status(pid)
            for pid in self.projects
            if self.get_project_status(pid) is not None
        ]


if __name__ == "__main__":
    engine = OrchestrationEngine()
    
    project = engine.create_project(
        name="Test Project",
        goal="Create a simple REST API",
        tech_stack=["python", "fastapi"],
    )
    
    print(f"Created project: {project.project_id}")
    print(f"Status: {engine.get_project_status(project.project_id)}")
