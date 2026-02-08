"""
Task Queue System for AURORA-DEV.

This module provides a Celery-based distributed task queue with Redis
as the message broker. Supports priority levels, task status tracking,
and robust error handling.
"""
from celery import Celery
from aurora_dev.core.task_queue.config import CeleryConfig


app = Celery("aurora_dev")
app.config_from_object(CeleryConfig)

from aurora_dev.core.task_queue.manager import TaskManager
from aurora_dev.core.task_queue.tasks import (
    execute_agent_task,
    process_reflexion,
    aggregate_results,
)

__all__ = [
    "app",
    "TaskManager",
    "execute_agent_task",
    "process_reflexion",
    "aggregate_results",
]
