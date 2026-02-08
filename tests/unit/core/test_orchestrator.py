"""
Unit tests for Orchestrator components.

Tests OrchestrationEngine, TaskScheduler, and AgentLifecycleManager.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, UTC

from aurora_dev.core.orchestrator.scheduler import (
    TaskNode,
    DependencyGraph,
    TaskScheduler,
)


class TestTaskNode:
    """Tests for TaskNode dataclass."""
    
    def test_initialization(self) -> None:
        """Test node initialization."""
        node = TaskNode(
            task_id="task-1",
            agent_type="backend",
            operation="implement",
            parameters={"feature": "auth"},
        )
        
        assert node.task_id == "task-1"
        assert node.agent_type == "backend"
        assert node.operation == "implement"
        assert node.dependencies == []
    
    def test_is_ready_no_dependencies(self) -> None:
        """Test node is ready with no dependencies."""
        node = TaskNode(
            task_id="task-1",
            agent_type="backend",
            operation="implement",
        )
        
        completed = set()
        assert node.is_ready(completed) is True
    
    def test_is_ready_with_completed_dependencies(self) -> None:
        """Test node is ready when dependencies completed."""
        node = TaskNode(
            task_id="task-2",
            agent_type="backend",
            operation="implement",
            dependencies=["task-1"],
        )
        
        completed = {"task-1"}
        assert node.is_ready(completed) is True
    
    def test_is_ready_with_pending_dependencies(self) -> None:
        """Test node not ready when dependencies pending."""
        node = TaskNode(
            task_id="task-2",
            agent_type="backend",
            operation="implement",
            dependencies=["task-1"],
        )
        
        completed = set()
        assert node.is_ready(completed) is False


class TestDependencyGraph:
    """Tests for DependencyGraph."""
    
    def test_add_node(self) -> None:
        """Test adding nodes to graph."""
        graph = DependencyGraph()
        
        node = TaskNode(
            task_id="task-1",
            agent_type="backend",
            operation="implement",
        )
        
        graph.add_node(node)
        
        assert "task-1" in graph.nodes
    
    def test_add_edge(self) -> None:
        """Test adding edges between nodes."""
        graph = DependencyGraph()
        
        node1 = TaskNode(task_id="task-1", agent_type="backend", operation="design")
        node2 = TaskNode(task_id="task-2", agent_type="backend", operation="implement")
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge("task-1", "task-2")
        
        assert "task-2" in graph.edges["task-1"]
    
    def test_get_roots(self) -> None:
        """Test finding root nodes (no dependencies)."""
        graph = DependencyGraph()
        
        node1 = TaskNode(task_id="root", agent_type="architect", operation="design")
        node2 = TaskNode(task_id="child", agent_type="backend", operation="implement", dependencies=["root"])
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge("root", "child")
        
        roots = graph.get_roots()
        
        assert len(roots) == 1
        assert roots[0].task_id == "root"
    
    def test_topological_sort(self) -> None:
        """Test topological sorting of nodes."""
        graph = DependencyGraph()
        
        # Create a simple dependency chain: A -> B -> C
        node_a = TaskNode(task_id="A", agent_type="architect", operation="design")
        node_b = TaskNode(task_id="B", agent_type="backend", operation="implement", dependencies=["A"])
        node_c = TaskNode(task_id="C", agent_type="tester", operation="test", dependencies=["B"])
        
        graph.add_node(node_a)
        graph.add_node(node_b)
        graph.add_node(node_c)
        graph.add_edge("A", "B")
        graph.add_edge("B", "C")
        
        sorted_nodes = graph.topological_sort()
        sorted_ids = [n.task_id for n in sorted_nodes]
        
        # A must come before B, B must come before C
        assert sorted_ids.index("A") < sorted_ids.index("B")
        assert sorted_ids.index("B") < sorted_ids.index("C")
    
    def test_detect_cycle(self) -> None:
        """Test cycle detection."""
        graph = DependencyGraph()
        
        # Create a cycle: A -> B -> A
        node_a = TaskNode(task_id="A", agent_type="backend", operation="op1")
        node_b = TaskNode(task_id="B", agent_type="backend", operation="op2")
        
        graph.add_node(node_a)
        graph.add_node(node_b)
        graph.add_edge("A", "B")
        graph.add_edge("B", "A")
        
        assert graph.has_cycle() is True
    
    def test_no_cycle(self) -> None:
        """Test no cycle in valid graph."""
        graph = DependencyGraph()
        
        node_a = TaskNode(task_id="A", agent_type="backend", operation="op1")
        node_b = TaskNode(task_id="B", agent_type="backend", operation="op2")
        
        graph.add_node(node_a)
        graph.add_node(node_b)
        graph.add_edge("A", "B")
        
        assert graph.has_cycle() is False


class TestTaskScheduler:
    """Tests for TaskScheduler."""
    
    def test_initialization(self) -> None:
        """Test scheduler initialization."""
        scheduler = TaskScheduler()
        
        assert scheduler is not None
        assert len(scheduler._graph.nodes) == 0
    
    def test_add_task(self) -> None:
        """Test adding task to scheduler."""
        scheduler = TaskScheduler()
        
        scheduler.add_task(
            task_id="task-1",
            agent_type="backend",
            operation="implement",
            parameters={"feature": "auth"},
        )
        
        assert "task-1" in scheduler._graph.nodes
    
    def test_add_task_with_dependencies(self) -> None:
        """Test adding task with dependencies."""
        scheduler = TaskScheduler()
        
        scheduler.add_task(
            task_id="task-1",
            agent_type="architect",
            operation="design",
        )
        
        scheduler.add_task(
            task_id="task-2",
            agent_type="backend",
            operation="implement",
            dependencies=["task-1"],
        )
        
        # Check dependency is recorded
        node = scheduler._graph.nodes["task-2"]
        assert "task-1" in node.dependencies
    
    def test_get_executable_tasks(self) -> None:
        """Test getting tasks ready for execution."""
        scheduler = TaskScheduler()
        
        scheduler.add_task("task-1", "architect", "design")
        scheduler.add_task("task-2", "backend", "implement", dependencies=["task-1"])
        scheduler.add_task("task-3", "frontend", "implement", dependencies=["task-1"])
        
        # Initially only task-1 is ready
        ready = scheduler.get_executable_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "task-1"
        
        # After completing task-1, tasks 2 and 3 should be ready
        scheduler.mark_completed("task-1")
        ready = scheduler.get_executable_tasks()
        
        assert len(ready) == 2
        task_ids = {t.task_id for t in ready}
        assert "task-2" in task_ids
        assert "task-3" in task_ids
    
    def test_parallel_groups(self) -> None:
        """Test identifying parallel execution groups."""
        scheduler = TaskScheduler()
        
        # Two independent tasks that can run in parallel
        scheduler.add_task("task-a", "backend", "implement")
        scheduler.add_task("task-b", "frontend", "implement")
        
        groups = scheduler.get_parallel_groups()
        
        # Both tasks should be in the same parallel group
        assert len(groups) >= 1
        first_group_ids = {t.task_id for t in groups[0]}
        assert "task-a" in first_group_ids
        assert "task-b" in first_group_ids
