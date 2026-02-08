"""
Task Manager for AURORA-DEV queue operations.

Provides a high-level interface for submitting, tracking, and
managing tasks in the Celery queue system.
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generator, Optional
from uuid import uuid4

import redis

from aurora_dev.core.config import get_settings
from aurora_dev.core.task_queue.models import (
    TaskMetadata,
    TaskPayload,
    TaskPriority,
    TaskResult,
    TaskStatus,
    TaskType,
)


logger = logging.getLogger(__name__)


@dataclass
class TaskManager:
    """Manager for task queue operations.
    
    Provides methods for submitting tasks, tracking status,
    and managing the task lifecycle.
    
    Attributes:
        redis_client: Redis client for task tracking.
        task_prefix: Prefix for Redis keys.
        result_ttl: Time-to-live for results in seconds.
    """
    
    redis_client: redis.Redis = field(init=False)
    task_prefix: str = "aurora:task:"
    result_ttl: int = 3600
    
    def __post_init__(self) -> None:
        """Initialize Redis connection."""
        settings = get_settings()
        self.redis_client = redis.from_url(
            settings.redis.url,
            decode_responses=True,
        )
        logger.info("TaskManager initialized with Redis backend")
    
    def submit(
        self,
        operation: str,
        parameters: dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        timeout_seconds: int = 300,
        tags: Optional[list[str]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """Submit a new task to the queue.
        
        Args:
            operation: Operation to perform.
            parameters: Operation parameters.
            priority: Task priority level.
            project_id: Associated project ID.
            agent_id: Optional assigned agent ID.
            timeout_seconds: Task timeout.
            tags: Optional categorization tags.
            context: Optional execution context.
            
        Returns:
            Task ID of the submitted task.
        """
        from aurora_dev.core.task_queue.tasks import execute_agent_task
        
        metadata = TaskMetadata(
            task_id=str(uuid4()),
            task_type=TaskType.AGENT_EXECUTION,
            priority=priority,
            status=TaskStatus.QUEUED,
            project_id=project_id,
            agent_id=agent_id,
            timeout_seconds=timeout_seconds,
            tags=tags or [],
        )
        
        payload = TaskPayload(
            metadata=metadata,
            operation=operation,
            parameters=parameters,
            context=context or {},
        )
        
        self._store_task_metadata(metadata)
        
        queue_name = self._get_queue_for_priority(priority)
        
        try:
            execute_agent_task.apply_async(
                args=[payload.to_dict()],
                task_id=metadata.task_id,
                queue=queue_name,
                priority=priority.value,
            )
            logger.info(f"Task {metadata.task_id} submitted to queue {queue_name}")
        except Exception as e:
            logger.error(f"Failed to submit task {metadata.task_id}: {e}")
            self._update_task_status(metadata.task_id, TaskStatus.FAILED, error=str(e))
            raise
        
        return metadata.task_id
    
    def submit_reflexion(
        self,
        task_id: str,
        attempt_result: dict[str, Any],
        project_id: Optional[str] = None,
    ) -> str:
        """Submit a reflexion task for a failed attempt.
        
        Args:
            task_id: Original task ID that failed.
            attempt_result: Result from the failed attempt.
            project_id: Associated project ID.
            
        Returns:
            Reflexion task ID.
        """
        from aurora_dev.core.task_queue.tasks import process_reflexion
        
        metadata = TaskMetadata(
            task_id=str(uuid4()),
            task_type=TaskType.REFLEXION,
            priority=TaskPriority.HIGH,
            status=TaskStatus.QUEUED,
            project_id=project_id,
            parent_task_id=task_id,
        )
        
        self._store_task_metadata(metadata)
        
        try:
            process_reflexion.apply_async(
                args=[task_id, attempt_result],
                task_id=metadata.task_id,
                queue="high",
                priority=TaskPriority.HIGH.value,
            )
            logger.info(f"Reflexion task {metadata.task_id} submitted for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to submit reflexion task: {e}")
            self._update_task_status(metadata.task_id, TaskStatus.FAILED, error=str(e))
            raise
        
        return metadata.task_id
    
    def get_status(self, task_id: str) -> Optional[TaskMetadata]:
        """Get the current status of a task.
        
        Args:
            task_id: Task identifier.
            
        Returns:
            TaskMetadata if found, None otherwise.
        """
        key = f"{self.task_prefix}{task_id}"
        data = self.redis_client.get(key)
        
        if data is None:
            return None
        
        return TaskMetadata.from_dict(json.loads(data))
    
    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get the result of a completed task.
        
        Args:
            task_id: Task identifier.
            
        Returns:
            TaskResult if available, None otherwise.
        """
        key = f"{self.task_prefix}{task_id}:result"
        data = self.redis_client.get(key)
        
        if data is None:
            return None
        
        result_data = json.loads(data)
        return TaskResult(
            task_id=result_data["task_id"],
            status=TaskStatus(result_data["status"]),
            output=result_data.get("output"),
            error=result_data.get("error"),
            duration_seconds=result_data.get("duration_seconds", 0.0),
            metadata=result_data.get("metadata", {}),
        )
    
    def cancel(self, task_id: str) -> bool:
        """Cancel a pending or running task.
        
        Args:
            task_id: Task identifier.
            
        Returns:
            True if task was cancelled, False otherwise.
        """
        from aurora_dev.core.task_queue import app
        
        try:
            app.control.revoke(task_id, terminate=True)
            self._update_task_status(task_id, TaskStatus.CANCELLED)
            logger.info(f"Task {task_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    def list_tasks(
        self,
        project_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 100,
    ) -> Generator[TaskMetadata, None, None]:
        """List tasks with optional filtering.
        
        Args:
            project_id: Filter by project ID.
            status: Filter by task status.
            limit: Maximum number of tasks to return.
            
        Yields:
            TaskMetadata for matching tasks.
        """
        pattern = f"{self.task_prefix}*"
        count = 0
        
        for key in self.redis_client.scan_iter(match=pattern):
            if ":result" in key:
                continue
                
            if count >= limit:
                break
                
            data = self.redis_client.get(key)
            if data is None:
                continue
                
            metadata = TaskMetadata.from_dict(json.loads(data))
            
            if project_id and metadata.project_id != project_id:
                continue
            if status and metadata.status != status:
                continue
                
            yield metadata
            count += 1
    
    def get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics.
        
        Returns:
            Dictionary with queue statistics.
        """
        from aurora_dev.core.task_queue import app
        
        try:
            inspect = app.control.inspect()
            active = inspect.active() or {}
            reserved = inspect.reserved() or {}
            scheduled = inspect.scheduled() or {}
            
            return {
                "active_tasks": sum(len(tasks) for tasks in active.values()),
                "reserved_tasks": sum(len(tasks) for tasks in reserved.values()),
                "scheduled_tasks": sum(len(tasks) for tasks in scheduled.values()),
                "workers": list(active.keys()),
            }
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {"error": str(e)}
    
    def store_result(
        self,
        task_id: str,
        status: TaskStatus,
        output: Any = None,
        error: Optional[str] = None,
        duration_seconds: float = 0.0,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Store task result in Redis.
        
        Args:
            task_id: Task identifier.
            status: Final task status.
            output: Task output data.
            error: Optional error message.
            duration_seconds: Execution duration.
            metadata: Additional result metadata.
        """
        result = TaskResult(
            task_id=task_id,
            status=status,
            output=output,
            error=error,
            duration_seconds=duration_seconds,
            metadata=metadata or {},
        )
        
        key = f"{self.task_prefix}{task_id}:result"
        self.redis_client.setex(key, self.result_ttl, json.dumps(result.to_dict()))
        self._update_task_status(task_id, status)
        
        logger.info(f"Stored result for task {task_id}: {status.value}")
    
    def _store_task_metadata(self, metadata: TaskMetadata) -> None:
        """Store task metadata in Redis.
        
        Args:
            metadata: Task metadata to store.
        """
        key = f"{self.task_prefix}{metadata.task_id}"
        self.redis_client.setex(
            key,
            self.result_ttl * 24,
            json.dumps(metadata.to_dict()),
        )
    
    def _update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        error: Optional[str] = None,
    ) -> None:
        """Update task status in Redis.
        
        Args:
            task_id: Task identifier.
            status: New task status.
            error: Optional error message.
        """
        metadata = self.get_status(task_id)
        if metadata is None:
            return
            
        metadata.status = status
        
        if status == TaskStatus.RUNNING and metadata.started_at is None:
            metadata.started_at = datetime.now(timezone.utc)
        elif status in {TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED}:
            metadata.completed_at = datetime.now(timezone.utc)
            
        if error:
            metadata.extra["error"] = error
            
        self._store_task_metadata(metadata)
    
    def _get_queue_for_priority(self, priority: TaskPriority) -> str:
        """Get queue name for priority level.
        
        Args:
            priority: Task priority level.
            
        Returns:
            Queue name string.
        """
        priority_queue_map = {
            TaskPriority.CRITICAL: "critical",
            TaskPriority.HIGH: "high",
            TaskPriority.MEDIUM: "default",
            TaskPriority.LOW: "low",
            TaskPriority.BACKGROUND: "low",
        }
        return priority_queue_map.get(priority, "default")


if __name__ == "__main__":
    manager = TaskManager()
    
    task_id = manager.submit(
        operation="implement_endpoint",
        parameters={"endpoint": "/api/users", "method": "GET"},
        priority=TaskPriority.HIGH,
        project_id="proj-123",
    )
    print(f"Submitted task: {task_id}")
    
    status = manager.get_status(task_id)
    if status:
        print(f"Task status: {status.status.value}")
