"""
Task Scheduler for AURORA-DEV orchestration.

Provides task scheduling with dependency resolution,
parallel execution groups, and resource allocation.
"""
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generator, Optional
from uuid import uuid4


logger = logging.getLogger(__name__)


class DependencyStatus(Enum):
    """Status of task dependencies.
    
    Indicates whether a task's dependencies are satisfied.
    """
    
    PENDING = "pending"
    SATISFIED = "satisfied"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class ScheduledTask:
    """A task scheduled for execution.
    
    Attributes:
        task_id: Unique task identifier.
        operation: Operation to perform.
        parameters: Operation parameters.
        dependencies: Task IDs this task depends on.
        priority: Numeric priority (higher = more important).
        estimated_duration: Estimated duration in seconds.
        assigned_agent: Optional assigned agent type.
        group_id: Optional group for parallel execution.
        scheduled_at: Scheduling timestamp.
        status: Current dependency status.
    """
    
    task_id: str = field(default_factory=lambda: str(uuid4()))
    operation: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    priority: int = 5
    estimated_duration: int = 60
    assigned_agent: Optional[str] = None
    group_id: Optional[str] = None
    scheduled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: DependencyStatus = DependencyStatus.PENDING
    
    @property
    def has_dependencies(self) -> bool:
        """Check if task has dependencies.
        
        Returns:
            True if task has dependencies.
        """
        return len(self.dependencies) > 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "task_id": self.task_id,
            "operation": self.operation,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "estimated_duration": self.estimated_duration,
            "assigned_agent": self.assigned_agent,
            "group_id": self.group_id,
            "scheduled_at": self.scheduled_at.isoformat(),
            "status": self.status.value,
        }


@dataclass
class ExecutionGroup:
    """Group of tasks for parallel execution.
    
    Attributes:
        group_id: Unique group identifier.
        tasks: Tasks in this group.
        max_concurrent: Maximum concurrent tasks.
        created_at: Group creation timestamp.
    """
    
    group_id: str = field(default_factory=lambda: str(uuid4()))
    tasks: list[ScheduledTask] = field(default_factory=list)
    max_concurrent: int = 4
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def task_ids(self) -> list[str]:
        """Get all task IDs in this group.
        
        Returns:
            List of task IDs.
        """
        return [t.task_id for t in self.tasks]
    
    def add_task(self, task: ScheduledTask) -> None:
        """Add a task to the group.
        
        Args:
            task: Task to add.
        """
        task.group_id = self.group_id
        self.tasks.append(task)


class TaskScheduler:
    """Scheduler for task execution with dependency resolution.
    
    Manages task scheduling, dependency tracking, and
    parallel execution group assignment.
    
    Attributes:
        tasks: All scheduled tasks.
        completed_tasks: Set of completed task IDs.
        failed_tasks: Set of failed task IDs.
        groups: Execution groups.
    """
    
    def __init__(self) -> None:
        """Initialize the task scheduler."""
        self.tasks: dict[str, ScheduledTask] = {}
        self.completed_tasks: set[str] = set()
        self.failed_tasks: set[str] = set()
        self.groups: dict[str, ExecutionGroup] = {}
        self._dependency_graph: dict[str, set[str]] = defaultdict(set)
        self._reverse_graph: dict[str, set[str]] = defaultdict(set)
        
        logger.info("TaskScheduler initialized")
    
    def schedule(
        self,
        operation: str,
        parameters: Optional[dict[str, Any]] = None,
        dependencies: Optional[list[str]] = None,
        priority: int = 5,
        estimated_duration: int = 60,
        assigned_agent: Optional[str] = None,
    ) -> str:
        """Schedule a new task.
        
        Args:
            operation: Operation to perform.
            parameters: Operation parameters.
            dependencies: Task IDs this task depends on.
            priority: Numeric priority.
            estimated_duration: Estimated duration in seconds.
            assigned_agent: Optional assigned agent type.
            
        Returns:
            Scheduled task ID.
        """
        task = ScheduledTask(
            operation=operation,
            parameters=parameters or {},
            dependencies=dependencies or [],
            priority=priority,
            estimated_duration=estimated_duration,
            assigned_agent=assigned_agent,
        )
        
        self.tasks[task.task_id] = task
        
        for dep_id in task.dependencies:
            self._dependency_graph[task.task_id].add(dep_id)
            self._reverse_graph[dep_id].add(task.task_id)
        
        self._update_task_status(task)
        
        logger.debug(f"Scheduled task: {task.task_id} ({operation})")
        
        return task.task_id
    
    def schedule_batch(
        self,
        tasks: list[dict[str, Any]],
    ) -> list[str]:
        """Schedule multiple tasks at once.
        
        Args:
            tasks: List of task definitions.
            
        Returns:
            List of scheduled task IDs.
        """
        task_ids = []
        
        for task_def in tasks:
            task_id = self.schedule(
                operation=task_def.get("operation", ""),
                parameters=task_def.get("parameters"),
                dependencies=task_def.get("dependencies"),
                priority=task_def.get("priority", 5),
                estimated_duration=task_def.get("estimated_duration", 60),
                assigned_agent=task_def.get("assigned_agent"),
            )
            task_ids.append(task_id)
        
        logger.info(f"Scheduled batch of {len(task_ids)} tasks")
        
        return task_ids
    
    def get_ready_tasks(self) -> Generator[ScheduledTask, None, None]:
        """Get tasks ready for execution.
        
        Tasks are ready when all dependencies are satisfied.
        Yields tasks in priority order.
        
        Yields:
            Tasks ready for execution.
        """
        ready = [
            task for task in self.tasks.values()
            if task.status == DependencyStatus.SATISFIED
            and task.task_id not in self.completed_tasks
            and task.task_id not in self.failed_tasks
        ]
        
        ready.sort(key=lambda t: (-t.priority, t.scheduled_at))
        
        for task in ready:
            yield task
    
    def get_next_batch(
        self,
        max_tasks: int = 10,
    ) -> list[ScheduledTask]:
        """Get next batch of tasks for parallel execution.
        
        Args:
            max_tasks: Maximum tasks to return.
            
        Returns:
            List of tasks ready for execution.
        """
        batch = []
        
        for task in self.get_ready_tasks():
            if len(batch) >= max_tasks:
                break
            batch.append(task)
        
        return batch
    
    def mark_completed(self, task_id: str) -> None:
        """Mark a task as completed.
        
        Args:
            task_id: Task identifier.
        """
        if task_id not in self.tasks:
            logger.warning(f"Task not found: {task_id}")
            return
        
        self.completed_tasks.add(task_id)
        logger.info(f"Task completed: {task_id}")
        
        for dependent_id in self._reverse_graph.get(task_id, set()):
            if dependent_id in self.tasks:
                self._update_task_status(self.tasks[dependent_id])
    
    def mark_failed(self, task_id: str) -> None:
        """Mark a task as failed.
        
        Also marks dependent tasks as blocked.
        
        Args:
            task_id: Task identifier.
        """
        if task_id not in self.tasks:
            logger.warning(f"Task not found: {task_id}")
            return
        
        self.failed_tasks.add(task_id)
        logger.warning(f"Task failed: {task_id}")
        
        for dependent_id in self._reverse_graph.get(task_id, set()):
            if dependent_id in self.tasks:
                self.tasks[dependent_id].status = DependencyStatus.BLOCKED
    
    def _update_task_status(self, task: ScheduledTask) -> None:
        """Update task dependency status.
        
        Args:
            task: Task to update.
        """
        if not task.has_dependencies:
            task.status = DependencyStatus.SATISFIED
            return
        
        deps = self._dependency_graph.get(task.task_id, set())
        
        if any(d in self.failed_tasks for d in deps):
            task.status = DependencyStatus.BLOCKED
        elif all(d in self.completed_tasks for d in deps):
            task.status = DependencyStatus.SATISFIED
        else:
            task.status = DependencyStatus.PENDING
    
    def create_parallel_group(
        self,
        task_ids: list[str],
        max_concurrent: int = 4,
    ) -> str:
        """Create a parallel execution group.
        
        Args:
            task_ids: Task IDs to add to group.
            max_concurrent: Maximum concurrent executions.
            
        Returns:
            Group identifier.
        """
        group = ExecutionGroup(max_concurrent=max_concurrent)
        
        for task_id in task_ids:
            if task_id in self.tasks:
                group.add_task(self.tasks[task_id])
        
        self.groups[group.group_id] = group
        logger.info(f"Created execution group: {group.group_id} with {len(group.tasks)} tasks")
        
        return group.group_id
    
    def resolve_execution_order(self) -> list[list[str]]:
        """Resolve optimal execution order using topological sort.
        
        Groups tasks into levels where each level can run in parallel.
        
        Returns:
            List of task ID lists, where each inner list is a parallel level.
        """
        in_degree: dict[str, int] = defaultdict(int)
        
        for task_id in self.tasks:
            for dep in self._dependency_graph.get(task_id, set()):
                in_degree[task_id] += 1
        
        levels: list[list[str]] = []
        remaining = set(self.tasks.keys()) - self.completed_tasks - self.failed_tasks
        
        while remaining:
            level = [
                tid for tid in remaining
                if in_degree.get(tid, 0) == 0
            ]
            
            if not level:
                logger.error("Circular dependency detected")
                break
            
            levels.append(level)
            
            for tid in level:
                remaining.discard(tid)
                for dependent in self._reverse_graph.get(tid, set()):
                    if dependent in remaining:
                        in_degree[dependent] -= 1
        
        logger.debug(f"Resolved {len(levels)} execution levels")
        
        return levels
    
    def get_statistics(self) -> dict[str, Any]:
        """Get scheduler statistics.
        
        Returns:
            Dictionary with scheduler stats.
        """
        total = len(self.tasks)
        completed = len(self.completed_tasks)
        failed = len(self.failed_tasks)
        pending = total - completed - failed
        
        ready = sum(
            1 for t in self.tasks.values()
            if t.status == DependencyStatus.SATISFIED
            and t.task_id not in self.completed_tasks
            and t.task_id not in self.failed_tasks
        )
        
        blocked = sum(
            1 for t in self.tasks.values()
            if t.status == DependencyStatus.BLOCKED
        )
        
        return {
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "ready": ready,
            "blocked": blocked,
            "groups": len(self.groups),
            "completion_rate": completed / total if total > 0 else 0,
        }
    
    def clear_completed(self) -> int:
        """Clear completed tasks from scheduler.
        
        Returns:
            Number of tasks cleared.
        """
        count = 0
        
        for task_id in list(self.completed_tasks):
            if task_id in self.tasks:
                del self.tasks[task_id]
                count += 1
        
        logger.info(f"Cleared {count} completed tasks")
        
        return count


if __name__ == "__main__":
    scheduler = TaskScheduler()
    
    task1 = scheduler.schedule(
        operation="setup_database",
        priority=10,
    )
    
    task2 = scheduler.schedule(
        operation="create_models",
        dependencies=[task1],
        priority=8,
    )
    
    task3 = scheduler.schedule(
        operation="create_api",
        dependencies=[task2],
        priority=7,
    )
    
    print(f"Execution order: {scheduler.resolve_execution_order()}")
    print(f"Stats: {scheduler.get_statistics()}")
    
    scheduler.mark_completed(task1)
    
    ready = list(scheduler.get_ready_tasks())
    print(f"Ready tasks: {[t.operation for t in ready]}")
