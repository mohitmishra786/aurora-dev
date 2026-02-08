"""
Unit tests for Orchestrator components.

Tests TaskScheduler and ScheduledTask.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from aurora_dev.core.orchestrator.scheduler import (
    ScheduledTask,
    TaskScheduler,
    DependencyStatus,
    ExecutionGroup,
)


class TestScheduledTask:
    """Tests for ScheduledTask dataclass."""
    
    def test_initialization(self) -> None:
        """Test task initialization."""
        task = ScheduledTask(
            task_id="task-1",
            operation="implement",
            parameters={"feature": "auth"},
            dependencies=[],
            priority=5,
        )
        
        assert task.task_id == "task-1"
        assert task.operation == "implement"
        assert task.parameters == {"feature": "auth"}
        assert task.priority == 5
    
    def test_has_dependencies_false(self) -> None:
        """Test task with no dependencies."""
        task = ScheduledTask(
            task_id="task-1",
            operation="implement",
            dependencies=[],
        )
        
        assert task.has_dependencies is False
    
    def test_has_dependencies_true(self) -> None:
        """Test task with dependencies."""
        task = ScheduledTask(
            task_id="task-2",
            operation="implement",
            dependencies=["task-1"],
        )
        
        assert task.has_dependencies is True
    
    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        task = ScheduledTask(
            task_id="task-1",
            operation="test",
            parameters={"key": "value"},
        )
        
        result = task.to_dict()
        
        assert result["task_id"] == "task-1"
        assert result["operation"] == "test"
        assert "parameters" in result


class TestExecutionGroup:
    """Tests for ExecutionGroup."""
    
    def test_initialization(self) -> None:
        """Test group initialization."""
        group = ExecutionGroup(
            group_id="group-1",
            max_concurrent=4,
        )
        
        assert group.group_id == "group-1"
        assert group.max_concurrent == 4
        assert len(group.tasks) == 0
    
    def test_add_task(self) -> None:
        """Test adding task to group."""
        group = ExecutionGroup(group_id="group-1")
        task = ScheduledTask(task_id="task-1", operation="test")
        
        group.add_task(task)
        
        assert len(group.tasks) == 1
        assert "task-1" in group.task_ids
    
    def test_task_ids(self) -> None:
        """Test getting task IDs from group."""
        group = ExecutionGroup(group_id="group-1")
        group.add_task(ScheduledTask(task_id="t1", operation="op1"))
        group.add_task(ScheduledTask(task_id="t2", operation="op2"))
        
        ids = group.task_ids
        
        assert "t1" in ids
        assert "t2" in ids


class TestTaskScheduler:
    """Tests for TaskScheduler."""
    
    def test_initialization(self) -> None:
        """Test scheduler initialization."""
        scheduler = TaskScheduler()
        
        assert scheduler is not None
        assert len(scheduler.tasks) == 0
    
    def test_schedule_task(self) -> None:
        """Test scheduling a task."""
        scheduler = TaskScheduler()
        
        task_id = scheduler.schedule(
            operation="implement",
            parameters={"feature": "auth"},
            priority=5,
        )
        
        assert task_id is not None
        assert task_id in scheduler.tasks
    
    def test_schedule_with_dependencies(self) -> None:
        """Test scheduling task with dependencies."""
        scheduler = TaskScheduler()
        
        task1_id = scheduler.schedule(operation="design")
        task2_id = scheduler.schedule(
            operation="implement",
            dependencies=[task1_id],
        )
        
        task2 = scheduler.tasks[task2_id]
        assert task1_id in task2.dependencies
    
    def test_get_ready_tasks(self) -> None:
        """Test getting tasks ready for execution."""
        scheduler = TaskScheduler()
        
        task1_id = scheduler.schedule(operation="design")
        task2_id = scheduler.schedule(operation="implement", dependencies=[task1_id])
        
        # Only task1 should be ready
        ready = list(scheduler.get_ready_tasks())
        ready_ids = [t.task_id for t in ready]
        
        assert task1_id in ready_ids
        assert task2_id not in ready_ids
    
    def test_mark_completed(self) -> None:
        """Test marking task as completed."""
        scheduler = TaskScheduler()
        
        task1_id = scheduler.schedule(operation="design")
        task2_id = scheduler.schedule(operation="implement", dependencies=[task1_id])
        
        scheduler.mark_completed(task1_id)
        
        # Now task2 should be ready
        ready = list(scheduler.get_ready_tasks())
        ready_ids = [t.task_id for t in ready]
        
        assert task2_id in ready_ids
    
    def test_schedule_batch(self) -> None:
        """Test batch scheduling."""
        scheduler = TaskScheduler()
        
        tasks = [
            {"operation": "design"},
            {"operation": "implement"},
            {"operation": "test"},
        ]
        
        task_ids = scheduler.schedule_batch(tasks)
        
        assert len(task_ids) == 3
        for tid in task_ids:
            assert tid in scheduler.tasks
