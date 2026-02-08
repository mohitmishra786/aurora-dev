"""
Celery worker configuration and management for AURORA-DEV.

Provides worker pool configuration, routing, and
concurrency management for distributed task execution.
"""
import logging
import signal
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from celery import Celery
from celery.signals import (
    worker_ready,
    worker_shutdown,
    task_prerun,
    task_postrun,
    task_failure,
)

from aurora_dev.core.config import get_settings


logger = logging.getLogger(__name__)


class WorkerPool(Enum):
    """Worker pool types for different workloads.
    
    Different pool types optimize for different task characteristics.
    """
    
    PREFORK = "prefork"
    EVENTLET = "eventlet"
    GEVENT = "gevent"
    SOLO = "solo"
    THREADS = "threads"


@dataclass
class WorkerConfig:
    """Configuration for a Celery worker.
    
    Attributes:
        name: Worker name identifier.
        queues: List of queues to consume.
        concurrency: Number of concurrent workers.
        pool: Worker pool type.
        prefetch_multiplier: Tasks to prefetch per worker.
        max_tasks_per_child: Tasks before worker restarts.
        max_memory_per_child: Memory limit in KB.
        time_limit: Hard time limit per task.
        soft_time_limit: Soft time limit per task.
    """
    
    name: str
    queues: list[str] = field(default_factory=lambda: ["default"])
    concurrency: int = 4
    pool: WorkerPool = WorkerPool.PREFORK
    prefetch_multiplier: int = 1
    max_tasks_per_child: int = 1000
    max_memory_per_child: Optional[int] = None
    time_limit: int = 600
    soft_time_limit: int = 300
    
    def to_argv(self) -> list[str]:
        """Convert configuration to Celery worker argv.
        
        Returns:
            List of command-line arguments.
        """
        argv = [
            "worker",
            f"--hostname={self.name}@%h",
            f"--queues={','.join(self.queues)}",
            f"--concurrency={self.concurrency}",
            f"--pool={self.pool.value}",
            f"--prefetch-multiplier={self.prefetch_multiplier}",
            f"--max-tasks-per-child={self.max_tasks_per_child}",
        ]
        
        if self.max_memory_per_child:
            argv.append(f"--max-memory-per-child={self.max_memory_per_child}")
            
        return argv


@dataclass
class WorkerStats:
    """Worker statistics for monitoring.
    
    Attributes:
        tasks_completed: Total tasks completed.
        tasks_failed: Total tasks failed.
        tasks_retried: Total tasks retried.
        avg_execution_time: Average execution time in seconds.
        active_tasks: Currently executing tasks.
    """
    
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_retried: int = 0
    avg_execution_time: float = 0.0
    active_tasks: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary.
        
        Returns:
            Dictionary representation of stats.
        """
        return {
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_retried": self.tasks_retried,
            "avg_execution_time": self.avg_execution_time,
            "active_tasks": self.active_tasks,
        }


class WorkerManager:
    """Manager for Celery worker lifecycle and monitoring.
    
    Provides methods for starting, stopping, and monitoring
    Celery workers with custom configurations.
    
    Attributes:
        app: Celery application instance.
        workers: Dictionary of active worker configurations.
        stats: Worker statistics.
    """
    
    def __init__(self, app: Optional[Celery] = None) -> None:
        """Initialize the worker manager.
        
        Args:
            app: Optional Celery application instance.
        """
        if app is None:
            from aurora_dev.core.task_queue import app as celery_app
            self.app = celery_app
        else:
            self.app = app
            
        self.workers: dict[str, WorkerConfig] = {}
        self.stats = WorkerStats()
        self._setup_signals()
        
        logger.info("WorkerManager initialized")
    
    def _setup_signals(self) -> None:
        """Set up Celery signal handlers."""
        
        @worker_ready.connect
        def on_worker_ready(sender: Any, **kwargs: Any) -> None:
            logger.info(f"Worker ready: {sender}")
        
        @worker_shutdown.connect
        def on_worker_shutdown(sender: Any, **kwargs: Any) -> None:
            logger.info(f"Worker shutdown: {sender}")
        
        @task_prerun.connect
        def on_task_prerun(
            task_id: str,
            task: Any,
            args: tuple,
            kwargs: dict,
            **extra: Any,
        ) -> None:
            self.stats.active_tasks += 1
            logger.debug(f"Task started: {task_id}")
        
        @task_postrun.connect
        def on_task_postrun(
            task_id: str,
            task: Any,
            args: tuple,
            kwargs: dict,
            retval: Any,
            state: str,
            **extra: Any,
        ) -> None:
            self.stats.active_tasks = max(0, self.stats.active_tasks - 1)
            if state == "SUCCESS":
                self.stats.tasks_completed += 1
            logger.debug(f"Task completed: {task_id} ({state})")
        
        @task_failure.connect
        def on_task_failure(
            task_id: str,
            exception: Exception,
            args: tuple,
            kwargs: dict,
            traceback: Any,
            einfo: Any,
            **extra: Any,
        ) -> None:
            self.stats.tasks_failed += 1
            logger.error(f"Task failed: {task_id} - {exception}")
    
    def register_worker(self, config: WorkerConfig) -> None:
        """Register a worker configuration.
        
        Args:
            config: Worker configuration to register.
        """
        self.workers[config.name] = config
        logger.info(f"Registered worker: {config.name}")
    
    def start_worker(
        self,
        name: str,
        queues: Optional[list[str]] = None,
        concurrency: int = 4,
        pool: WorkerPool = WorkerPool.PREFORK,
    ) -> None:
        """Start a Celery worker with configuration.
        
        Args:
            name: Worker name.
            queues: Queues to consume.
            concurrency: Number of concurrent workers.
            pool: Worker pool type.
        """
        config = WorkerConfig(
            name=name,
            queues=queues or ["default"],
            concurrency=concurrency,
            pool=pool,
        )
        
        self.register_worker(config)
        
        logger.info(f"Starting worker: {name}")
        self.app.worker_main(argv=config.to_argv())
    
    def stop_worker(self, name: str) -> bool:
        """Stop a running worker.
        
        Args:
            name: Worker name to stop.
            
        Returns:
            True if stop signal was sent.
        """
        try:
            self.app.control.broadcast(
                "shutdown",
                destination=[name],
            )
            logger.info(f"Shutdown signal sent to worker: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop worker {name}: {e}")
            return False
    
    def scale_workers(self, name: str, n: int) -> bool:
        """Scale the number of worker processes.
        
        Args:
            name: Worker name.
            n: Target number of processes (positive to add, negative to remove).
            
        Returns:
            True if scaling was successful.
        """
        try:
            if n > 0:
                self.app.control.pool_grow(n, destination=[name])
            else:
                self.app.control.pool_shrink(abs(n), destination=[name])
            logger.info(f"Scaled worker {name} by {n}")
            return True
        except Exception as e:
            logger.error(f"Failed to scale worker {name}: {e}")
            return False
    
    def get_active_workers(self) -> dict[str, Any]:
        """Get information about active workers.
        
        Returns:
            Dictionary with worker information.
        """
        try:
            inspect = self.app.control.inspect()
            return {
                "active": inspect.active() or {},
                "reserved": inspect.reserved() or {},
                "stats": inspect.stats() or {},
            }
        except Exception as e:
            logger.error(f"Failed to get active workers: {e}")
            return {"error": str(e)}
    
    def get_stats(self) -> dict[str, Any]:
        """Get worker statistics.
        
        Returns:
            Dictionary with worker stats.
        """
        return self.stats.to_dict()
    
    def purge_queue(self, queue: str) -> int:
        """Purge all messages from a queue.
        
        Args:
            queue: Queue name to purge.
            
        Returns:
            Number of messages purged.
        """
        try:
            count = self.app.control.purge()
            logger.info(f"Purged {count} messages from queue: {queue}")
            return count
        except Exception as e:
            logger.error(f"Failed to purge queue {queue}: {e}")
            return 0


def get_default_worker_configs() -> list[WorkerConfig]:
    """Get default worker configurations for AURORA-DEV.
    
    Returns:
        List of default worker configurations.
    """
    return [
        WorkerConfig(
            name="aurora-critical",
            queues=["critical"],
            concurrency=2,
            pool=WorkerPool.PREFORK,
            time_limit=300,
        ),
        WorkerConfig(
            name="aurora-high",
            queues=["high"],
            concurrency=4,
            pool=WorkerPool.PREFORK,
            time_limit=600,
        ),
        WorkerConfig(
            name="aurora-default",
            queues=["default"],
            concurrency=4,
            pool=WorkerPool.PREFORK,
            time_limit=600,
        ),
        WorkerConfig(
            name="aurora-low",
            queues=["low"],
            concurrency=2,
            pool=WorkerPool.PREFORK,
            time_limit=1200,
        ),
    ]


if __name__ == "__main__":
    manager = WorkerManager()
    
    configs = get_default_worker_configs()
    for config in configs:
        print(f"Worker: {config.name}, Queues: {config.queues}")
    
    print(f"Stats: {manager.get_stats()}")
