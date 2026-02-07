"""Unit tests for Task Definition System."""
import uuid

import pytest


class TestTaskDefinition:
    """Tests for TaskDefinition model."""

    def test_task_creation_with_defaults(self):
        """Test creating a task with default values."""
        from aurora_dev.agents.task import (
            TaskComplexity,
            TaskDefinition,
            TaskPriority,
            TaskStatus,
            TaskType,
        )
        
        task = TaskDefinition(
            name="Test Task",
            description="A test task",
            type=TaskType.WRITE_CODE,
        )
        
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL
        assert task.complexity == TaskComplexity.MEDIUM
        assert task.attempt_count == 0

    def test_task_with_custom_values(self):
        """Test creating a task with custom values."""
        from aurora_dev.agents.task import (
            TaskComplexity,
            TaskDefinition,
            TaskPriority,
            TaskType,
        )
        
        task = TaskDefinition(
            name="High Priority Task",
            description="Critical task",
            type=TaskType.FIX_BUG,
            priority=TaskPriority.CRITICAL,
            complexity=TaskComplexity.HIGH,
            timeout_seconds=600,
        )
        
        assert task.priority == TaskPriority.CRITICAL
        assert task.complexity == TaskComplexity.HIGH
        assert task.timeout_seconds == 600

    def test_task_is_ready_no_dependencies(self):
        """Test task readiness with no dependencies."""
        from aurora_dev.agents.task import TaskDefinition, TaskType
        
        task = TaskDefinition(
            name="Independent Task",
            description="No deps",
            type=TaskType.WRITE_CODE,
        )
        
        assert task.is_ready(set()) is True

    def test_task_is_ready_with_dependencies(self):
        """Test task readiness with dependencies."""
        from aurora_dev.agents.task import TaskDefinition, TaskType
        
        dep_id = str(uuid.uuid4())
        
        task = TaskDefinition(
            name="Dependent Task",
            description="Has deps",
            type=TaskType.WRITE_CODE,
            dependencies=[dep_id],
        )
        
        # Not ready when dependency not complete
        assert task.is_ready(set()) is False
        
        # Ready when dependency complete
        assert task.is_ready({dep_id}) is True

    def test_task_lifecycle(self):
        """Test task status transitions."""
        from aurora_dev.agents.task import (
            TaskDefinition,
            TaskResult,
            TaskStatus,
            TaskType,
        )
        
        task = TaskDefinition(
            name="Lifecycle Task",
            description="Test lifecycle",
            type=TaskType.WRITE_CODE,
        )
        
        assert task.status == TaskStatus.PENDING
        
        # Start task
        task.mark_started()
        assert task.status == TaskStatus.RUNNING
        assert task.attempt_count == 1
        assert task.started_at is not None
        
        # Complete task
        result = TaskResult(
            success=True,
            output="Task completed",
            artifacts=["file.py"],
        )
        task.mark_completed(result)
        
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert task.result is not None
        assert task.result.success is True

    def test_task_can_retry(self):
        """Test retry logic."""
        from aurora_dev.agents.task import TaskDefinition, TaskStatus, TaskType
        
        task = TaskDefinition(
            name="Retry Task",
            description="Test retry",
            type=TaskType.WRITE_CODE,
            max_attempts=3,
        )
        
        # Initially can't retry (not failed)
        assert task.can_retry is False
        
        # After 1 failed attempt
        task.mark_started()
        task.mark_failed("Error 1")
        assert task.can_retry is True
        assert task.attempt_count == 1
        
        # After 2 failed attempts
        task.mark_started()
        task.mark_failed("Error 2")
        assert task.can_retry is True
        assert task.attempt_count == 2
        
        # After 3 failed attempts (max)
        task.mark_started()
        task.mark_failed("Error 3")
        assert task.can_retry is False
        assert task.attempt_count == 3


class TestTaskDependencyGraph:
    """Tests for TaskDependencyGraph."""

    def test_add_task(self):
        """Test adding tasks to graph."""
        from aurora_dev.agents.task import (
            TaskDefinition,
            TaskDependencyGraph,
            TaskType,
        )
        
        graph = TaskDependencyGraph()
        
        task = TaskDefinition(
            name="Task 1",
            description="First task",
            type=TaskType.WRITE_CODE,
        )
        
        graph.add_task(task)
        
        assert graph.task_count == 1
        assert graph.get_task(task.id) is task

    def test_get_ready_tasks(self):
        """Test getting ready tasks."""
        from aurora_dev.agents.task import (
            TaskDefinition,
            TaskDependencyGraph,
            TaskType,
        )
        
        graph = TaskDependencyGraph()
        
        task1 = TaskDefinition(
            id="task-1",
            name="Task 1",
            description="First task",
            type=TaskType.WRITE_CODE,
        )
        task2 = TaskDefinition(
            id="task-2",
            name="Task 2",
            description="Depends on task 1",
            type=TaskType.WRITE_CODE,
            dependencies=["task-1"],
        )
        
        graph.add_task(task1)
        graph.add_task(task2)
        
        # Initially only task1 is ready
        ready = graph.get_ready_tasks(completed=set())
        assert len(ready) == 1
        assert ready[0].id == "task-1"
        
        # After task1 completes, task2 is ready
        ready = graph.get_ready_tasks(completed={"task-1"})
        assert len(ready) == 2  # Both pending tasks are checked

    def test_topological_sort(self):
        """Test topological sorting of tasks."""
        from aurora_dev.agents.task import (
            TaskDefinition,
            TaskDependencyGraph,
            TaskType,
        )
        
        graph = TaskDependencyGraph()
        
        task1 = TaskDefinition(
            id="task-1",
            name="First",
            description="No deps",
            type=TaskType.WRITE_CODE,
        )
        task2 = TaskDefinition(
            id="task-2",
            name="Second",
            description="Depends on first",
            type=TaskType.WRITE_CODE,
            dependencies=["task-1"],
        )
        task3 = TaskDefinition(
            id="task-3",
            name="Third",
            description="Depends on second",
            type=TaskType.WRITE_CODE,
            dependencies=["task-2"],
        )
        
        # Add in reverse order
        graph.add_task(task3)
        graph.add_task(task2)
        graph.add_task(task1)
        
        sorted_tasks = graph.topological_sort()
        
        # task1 should come before task2, task2 before task3
        ids = [t.id for t in sorted_tasks]
        assert ids.index("task-1") < ids.index("task-2")
        assert ids.index("task-2") < ids.index("task-3")

    def test_cycle_detection(self):
        """Test that cycles are detected."""
        from aurora_dev.agents.task import (
            TaskDefinition,
            TaskDependencyGraph,
            TaskType,
        )
        
        graph = TaskDependencyGraph()
        
        task1 = TaskDefinition(
            id="task-1",
            name="Task 1",
            description="Depends on task 2 (cycle)",
            type=TaskType.WRITE_CODE,
            dependencies=["task-2"],
        )
        task2 = TaskDefinition(
            id="task-2",
            name="Task 2",
            description="Depends on task 1 (cycle)",
            type=TaskType.WRITE_CODE,
            dependencies=["task-1"],
        )
        
        graph.add_task(task1)
        
        # Adding task2 should raise ValueError due to cycle
        with pytest.raises(ValueError, match="cycle"):
            graph.add_task(task2)


class TestTaskResult:
    """Tests for TaskResult model."""

    def test_successful_result(self):
        """Test successful task result."""
        from aurora_dev.agents.task import TaskResult
        
        result = TaskResult(
            success=True,
            output="Task completed",
            artifacts=["/path/to/file.py"],
            metrics={"duration_seconds": 5.0},
        )
        
        assert result.success is True
        assert result.output == "Task completed"
        assert len(result.artifacts) == 1
        assert result.error is None

    def test_failed_result(self):
        """Test failed task result."""
        from aurora_dev.agents.task import TaskResult
        
        result = TaskResult(
            success=False,
            error="Task failed: timeout",
        )
        
        assert result.success is False
        assert result.error == "Task failed: timeout"
