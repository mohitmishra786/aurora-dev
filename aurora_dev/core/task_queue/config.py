"""
Celery configuration for AURORA-DEV task queue.

Provides centralized configuration for the Celery application
including broker settings, result backend, and task routing.
"""
from dataclasses import dataclass
from typing import ClassVar

from aurora_dev.core.config import get_settings


@dataclass
class CeleryConfig:
    """Celery configuration using Redis as broker and result backend.
    
    Attributes:
        broker_url: Redis connection URL for message broker.
        result_backend: Redis connection URL for result storage.
        task_serializer: Serialization format for tasks.
        result_serializer: Serialization format for results.
        accept_content: Accepted content types.
        timezone: Application timezone.
        enable_utc: Whether to use UTC timestamps.
        task_track_started: Track task started state.
        task_acks_late: Acknowledge tasks after completion.
        worker_prefetch_multiplier: Number of tasks to prefetch.
        task_default_queue: Default queue name.
        task_queues: Queue definitions with priorities.
        task_routes: Task routing configuration.
    """
    
    _settings: ClassVar = get_settings()
    
    broker_url: ClassVar[str] = _settings.redis.url
    result_backend: ClassVar[str] = _settings.redis.url
    task_serializer: ClassVar[str] = "json"
    result_serializer: ClassVar[str] = "json"
    accept_content: ClassVar[list[str]] = ["json"]
    timezone: ClassVar[str] = "UTC"
    enable_utc: ClassVar[bool] = True
    task_track_started: ClassVar[bool] = True
    task_acks_late: ClassVar[bool] = True
    worker_prefetch_multiplier: ClassVar[int] = 1
    task_default_queue: ClassVar[str] = "default"
    
    task_queues: ClassVar[dict] = {
        "critical": {"queue_arguments": {"x-max-priority": 10}},
        "high": {"queue_arguments": {"x-max-priority": 7}},
        "default": {"queue_arguments": {"x-max-priority": 5}},
        "low": {"queue_arguments": {"x-max-priority": 3}},
    }
    
    task_routes: ClassVar[dict] = {
        "aurora_dev.core.task_queue.tasks.execute_agent_task": {"queue": "default"},
        "aurora_dev.core.task_queue.tasks.process_reflexion": {"queue": "high"},
        "aurora_dev.core.task_queue.tasks.aggregate_results": {"queue": "low"},
    }
    
    task_annotations: ClassVar[dict] = {
        "aurora_dev.core.task_queue.tasks.execute_agent_task": {
            "rate_limit": "100/m",
            "max_retries": 3,
        },
        "aurora_dev.core.task_queue.tasks.process_reflexion": {
            "rate_limit": "50/m",
            "max_retries": 5,
        },
    }
    
    broker_connection_retry_on_startup: ClassVar[bool] = True
    result_expires: ClassVar[int] = 3600
    task_soft_time_limit: ClassVar[int] = 300
    task_time_limit: ClassVar[int] = 600
