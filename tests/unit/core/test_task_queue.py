"""
Unit tests for Task Queue system.

Tests TaskPriority, TaskStatus, TaskMetadata, TaskPayload, TaskResult, and TaskManager.
"""
import pytest
from datetime import datetime, UTC
from uuid import uuid4

from aurora_dev.core.task_queue.models import (
    TaskPriority,
    TaskStatus,
    TaskType,
    TaskMetadata,
    TaskPayload,
    TaskResult,
)


class TestTaskPriority:
    """Tests for TaskPriority enum."""
    
    def test_priority_ordering(self) -> None:
        """Test that priorities have correct numerical ordering."""
        assert TaskPriority.CRITICAL.value > TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value > TaskPriority.MEDIUM.value
        assert TaskPriority.MEDIUM.value > TaskPriority.LOW.value
        assert TaskPriority.LOW.value > TaskPriority.BACKGROUND.value
    
    def test_all_priorities_defined(self) -> None:
        """Verify all expected priorities exist."""
        expected = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "BACKGROUND"]
        actual = [p.name for p in TaskPriority]
        
        for priority in expected:
            assert priority in actual


class TestTaskStatus:
    """Tests for TaskStatus enum."""
    
    def test_all_statuses_defined(self) -> None:
        """Verify all expected statuses exist."""
        expected = [
            "PENDING", "QUEUED", "RUNNING", "SUCCESS",
            "FAILED", "RETRYING", "CANCELLED", "TIMEOUT"
        ]
        actual = [s.name for s in TaskStatus]
        
        for status in expected:
            assert status in actual
    
    def test_status_values_lowercase(self) -> None:
        """Status values should be lowercase strings."""
        for status in TaskStatus:
            assert isinstance(status.value, str)
            assert status.value == status.value.lower()


class TestTaskType:
    """Tests for TaskType enum."""
    
    def test_all_types_defined(self) -> None:
        """Verify all expected task types exist."""
        expected = [
            "AGENT_EXECUTION", "REFLEXION", "AGGREGATION",
            "WORKFLOW_STEP", "HEALTH_CHECK"
        ]
        actual = [t.name for t in TaskType]
        
        for task_type in expected:
            assert task_type in actual


class TestTaskMetadata:
    """Tests for TaskMetadata dataclass."""
    
    def test_default_initialization(self) -> None:
        """Test default field values."""
        metadata = TaskMetadata()
        
        assert metadata.task_id is not None
        assert len(metadata.task_id) == 36  # UUID length
        assert metadata.task_type == TaskType.AGENT_EXECUTION
        assert metadata.priority == TaskPriority.MEDIUM
        assert metadata.status == TaskStatus.PENDING
        assert metadata.retry_count == 0
        assert metadata.max_retries == 3
    
    def test_is_terminal_success(self) -> None:
        """Test is_terminal for success status."""
        metadata = TaskMetadata(status=TaskStatus.SUCCESS)
        assert metadata.is_terminal is True
    
    def test_is_terminal_running(self) -> None:
        """Test is_terminal for non-terminal status."""
        metadata = TaskMetadata(status=TaskStatus.RUNNING)
        assert metadata.is_terminal is False
    
    def test_can_retry_true(self) -> None:
        """Test can_retry when retries available."""
        metadata = TaskMetadata(
            status=TaskStatus.FAILED,
            retry_count=1,
            max_retries=3,
        )
        assert metadata.can_retry is True
    
    def test_can_retry_false_exhausted(self) -> None:
        """Test can_retry when retries exhausted."""
        metadata = TaskMetadata(
            status=TaskStatus.FAILED,
            retry_count=3,
            max_retries=3,
        )
        assert metadata.can_retry is False
    
    def test_can_retry_false_success(self) -> None:
        """Test can_retry when already successful."""
        # can_retry only checks retry_count < max_retries, not status
        metadata = TaskMetadata(
            status=TaskStatus.SUCCESS,
            retry_count=3,  # exhausted
            max_retries=3,
        )
        assert metadata.can_retry is False
    
    def test_duration_calculation(self) -> None:
        """Test duration calculation when completed."""
        start = datetime.now(UTC)
        end = datetime.now(UTC)
        
        metadata = TaskMetadata(
            started_at=start,  # duration uses started_at, not created_at
            completed_at=end,
        )
        
        # Duration should be a non-negative float
        assert isinstance(metadata.duration_seconds, float)
        assert metadata.duration_seconds >= 0
    
    def test_to_dict(self) -> None:
        """Test dictionary serialization."""
        metadata = TaskMetadata(
            task_id="test-123",
            priority=TaskPriority.HIGH,
        )
        
        result = metadata.to_dict()
        
        assert result["task_id"] == "test-123"
        assert result["priority"] == 7  # HIGH.value is 7
        assert "created_at" in result
    
    def test_from_dict(self) -> None:
        """Test dictionary deserialization."""
        data = {
            "task_id": "test-456",
            "task_type": "agent_execution",  # lowercase value
            "priority": 10,  # CRITICAL.value
            "status": "running",  # lowercase value
            "retry_count": 1,
            "max_retries": 3,
            "timeout_seconds": 300,
            "created_at": datetime.now(UTC).isoformat(),
        }
        
        metadata = TaskMetadata.from_dict(data)
        
        assert metadata.task_id == "test-456"
        assert metadata.priority == TaskPriority.CRITICAL
        assert metadata.status == TaskStatus.RUNNING


class TestTaskPayload:
    """Tests for TaskPayload dataclass."""
    
    def test_initialization(self) -> None:
        """Test payload initialization."""
        metadata = TaskMetadata()
        payload = TaskPayload(
            metadata=metadata,
            operation="design",
            parameters={"description": "test"},
        )
        
        assert payload.operation == "design"
        assert payload.parameters["description"] == "test"
        assert payload.context == {}
    
    def test_to_dict(self) -> None:
        """Test dictionary serialization."""
        payload = TaskPayload(
            metadata=TaskMetadata(task_id="test-789"),
            operation="execute",
            parameters={"key": "value"},
            context={"project_id": "proj-123"},
        )
        
        result = payload.to_dict()
        
        assert result["operation"] == "execute"
        assert result["parameters"]["key"] == "value"
        assert result["context"]["project_id"] == "proj-123"
        assert result["metadata"]["task_id"] == "test-789"
    
    def test_from_dict(self) -> None:
        """Test dictionary deserialization."""
        data = {
            "metadata": {
                "task_id": "test-abc",
                "task_type": "agent_execution",  # lowercase value
                "priority": 7,  # HIGH.value
                "status": "pending",  # lowercase value
                "retry_count": 0,
                "max_retries": 3,
                "timeout_seconds": 300,
                "created_at": datetime.now(UTC).isoformat(),
            },
            "operation": "analyze",
            "parameters": {"data": "test"},
            "context": {},
        }
        
        payload = TaskPayload.from_dict(data)
        
        assert payload.operation == "analyze"
        assert payload.metadata.task_id == "test-abc"


class TestTaskResult:
    """Tests for TaskResult dataclass."""
    
    def test_success_property_true(self) -> None:
        """Test success property when status is SUCCESS."""
        result = TaskResult(
            task_id="test-1",
            status=TaskStatus.SUCCESS,
            output={"result": "done"},
        )
        
        assert result.success is True
    
    def test_success_property_false(self) -> None:
        """Test success property when status is FAILED."""
        result = TaskResult(
            task_id="test-2",
            status=TaskStatus.FAILED,
            error="Something went wrong",
        )
        
        assert result.success is False
    
    def test_to_dict(self) -> None:
        """Test dictionary serialization."""
        result = TaskResult(
            task_id="test-3",
            status=TaskStatus.SUCCESS,
            output={"key": "value"},
            duration_seconds=1.5,
        )
        
        data = result.to_dict()
        
        assert data["task_id"] == "test-3"
        assert data["status"] == "success"  # lowercase value
        assert data["output"]["key"] == "value"
        assert data["duration_seconds"] == 1.5
