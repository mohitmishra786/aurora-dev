"""
Celery task definitions for AURORA-DEV.

Provides the core Celery tasks for agent execution, reflexion
processing, and result aggregation.
"""
import logging
import time
from datetime import datetime, timezone
from typing import Any

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded

from aurora_dev.core.task_queue.models import (
    TaskMetadata,
    TaskPayload,
    TaskResult,
    TaskStatus,
)


logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    soft_time_limit=300,
    time_limit=600,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
)
def execute_agent_task(self, payload_dict: dict[str, Any]) -> dict[str, Any]:
    """Execute an agent task.
    
    This is the main task for executing agent operations. It handles
    task lifecycle, error handling, and result storage.
    
    Args:
        self: Celery task instance (bound).
        payload_dict: Task payload as dictionary.
        
    Returns:
        TaskResult as dictionary.
        
    Raises:
        MaxRetriesExceededError: When max retries are exceeded.
        SoftTimeLimitExceeded: When task exceeds time limit.
    """
    from aurora_dev.core.task_queue.manager import TaskManager
    
    start_time = time.time()
    task_id = self.request.id
    manager = TaskManager()
    
    try:
        payload = TaskPayload.from_dict(payload_dict)
        logger.info(f"Executing task {task_id}: {payload.operation}")
        
        manager._update_task_status(task_id, TaskStatus.RUNNING)
        
        result = _execute_operation(payload)
        
        duration = time.time() - start_time
        
        manager.store_result(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            output=result,
            duration_seconds=duration,
        )
        
        logger.info(f"Task {task_id} completed in {duration:.2f}s")
        
        return TaskResult(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            output=result,
            duration_seconds=duration,
        ).to_dict()
        
    except SoftTimeLimitExceeded:
        logger.error(f"Task {task_id} exceeded time limit")
        manager.store_result(
            task_id=task_id,
            status=TaskStatus.TIMEOUT,
            error="Task exceeded time limit",
            duration_seconds=time.time() - start_time,
        )
        raise
        
    except MaxRetriesExceededError:
        logger.error(f"Task {task_id} max retries exceeded")
        duration = time.time() - start_time
        manager.store_result(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error="Max retries exceeded",
            duration_seconds=duration,
        )
        
        manager.submit_reflexion(
            task_id=task_id,
            attempt_result={"error": "Max retries exceeded", "payload": payload_dict},
            project_id=payload_dict.get("metadata", {}).get("project_id"),
        )
        raise
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        
        metadata = manager.get_status(task_id)
        if metadata and metadata.can_retry:
            manager._update_task_status(task_id, TaskStatus.RETRYING)
            raise self.retry(exc=e)
        
        duration = time.time() - start_time
        manager.store_result(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=str(e),
            duration_seconds=duration,
        )
        raise


@shared_task(
    bind=True,
    max_retries=5,
    soft_time_limit=120,
    time_limit=180,
)
def process_reflexion(
    self,
    original_task_id: str,
    attempt_result: dict[str, Any],
) -> dict[str, Any]:
    """Process reflexion for a failed task.
    
    Generates a reflection and improved strategy for retry.
    
    Args:
        self: Celery task instance (bound).
        original_task_id: ID of the failed task.
        attempt_result: Result from the failed attempt.
        
    Returns:
        Reflexion result as dictionary.
    """
    from aurora_dev.core.reflexion import ReflexionEngine, TaskContext, AttemptResult
    from aurora_dev.core.task_queue.manager import TaskManager
    
    start_time = time.time()
    task_id = self.request.id
    manager = TaskManager()
    
    try:
        logger.info(f"Processing reflexion {task_id} for task {original_task_id}")
        
        manager._update_task_status(task_id, TaskStatus.RUNNING)
        
        engine = ReflexionEngine()
        
        task_context = TaskContext(
            task_id=original_task_id,
            description=attempt_result.get("payload", {}).get("operation", ""),
            requirements=[],
        )
        
        attempt = AttemptResult(
            success=False,
            output=None,
            error=attempt_result.get("error", "Unknown error"),
            approach_taken=str(attempt_result.get("payload", {})),
        )
        
        reflection = engine.generate_reflection(
            task=task_context,
            attempt=attempt,
            agent_id="system",
            attempt_number=1,
            trigger=None,
        )
        
        duration = time.time() - start_time
        
        result_data = {
            "original_task_id": original_task_id,
            "reflection": reflection.to_dict() if reflection else None,
            "improved_strategy": reflection.improved_strategy.approach if reflection else None,
        }
        
        manager.store_result(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            output=result_data,
            duration_seconds=duration,
        )
        
        logger.info(f"Reflexion {task_id} completed in {duration:.2f}s")
        
        return TaskResult(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            output=result_data,
            duration_seconds=duration,
        ).to_dict()
        
    except Exception as e:
        logger.error(f"Reflexion {task_id} failed: {e}")
        duration = time.time() - start_time
        manager.store_result(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=str(e),
            duration_seconds=duration,
        )
        raise


@shared_task(
    bind=True,
    max_retries=2,
    soft_time_limit=60,
    time_limit=120,
)
def aggregate_results(
    self,
    task_ids: list[str],
    aggregation_type: str = "merge",
) -> dict[str, Any]:
    """Aggregate results from multiple tasks.
    
    Args:
        self: Celery task instance (bound).
        task_ids: List of task IDs to aggregate.
        aggregation_type: Type of aggregation (merge, concat, custom).
        
    Returns:
        Aggregated result as dictionary.
    """
    from aurora_dev.core.task_queue.manager import TaskManager
    
    start_time = time.time()
    task_id = self.request.id
    manager = TaskManager()
    
    try:
        logger.info(f"Aggregating {len(task_ids)} tasks: {task_id}")
        
        manager._update_task_status(task_id, TaskStatus.RUNNING)
        
        results = []
        errors = []
        
        for tid in task_ids:
            result = manager.get_result(tid)
            if result:
                if result.success:
                    results.append(result.output)
                else:
                    errors.append({"task_id": tid, "error": result.error})
            else:
                errors.append({"task_id": tid, "error": "Result not found"})
        
        aggregated = _aggregate_by_type(results, aggregation_type)
        
        duration = time.time() - start_time
        
        output = {
            "aggregated": aggregated,
            "successful_count": len(results),
            "error_count": len(errors),
            "errors": errors if errors else None,
        }
        
        manager.store_result(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            output=output,
            duration_seconds=duration,
        )
        
        logger.info(f"Aggregation {task_id} completed: {len(results)} results merged")
        
        return TaskResult(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            output=output,
            duration_seconds=duration,
        ).to_dict()
        
    except Exception as e:
        logger.error(f"Aggregation {task_id} failed: {e}")
        duration = time.time() - start_time
        manager.store_result(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=str(e),
            duration_seconds=duration,
        )
        raise


def _execute_operation(payload: TaskPayload) -> Any:
    """Execute the operation specified in the payload.
    
    Args:
        payload: Task payload with operation details.
        
    Returns:
        Operation result.
        
    Raises:
        ValueError: If operation is not recognized.
    """
    operation = payload.operation
    parameters = payload.parameters
    context = payload.context
    
    logger.debug(f"Executing operation: {operation}")
    
    if operation == "implement_endpoint":
        return _execute_implement_endpoint(parameters, context)
    elif operation == "implement_service":
        return _execute_implement_service(parameters, context)
    elif operation == "generate_tests":
        return _execute_generate_tests(parameters, context)
    elif operation == "security_audit":
        return _execute_security_audit(parameters, context)
    elif operation == "code_review":
        return _execute_code_review(parameters, context)
    else:
        return _execute_generic(operation, parameters, context)


def _execute_implement_endpoint(
    parameters: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Execute endpoint implementation.
    
    Args:
        parameters: Endpoint parameters.
        context: Execution context.
        
    Returns:
        Implementation result.
    """
    from aurora_dev.agents.specialized.developers import BackendAgent
    
    agent = BackendAgent(project_id=context.get("project_id"))
    response = agent.implement_endpoint(
        endpoint=parameters.get("endpoint", "/api/resource"),
        method=parameters.get("method", "GET"),
        description=parameters.get("description", ""),
        request_schema=parameters.get("request_schema"),
        response_schema=parameters.get("response_schema"),
        language=parameters.get("language", "python"),
    )
    
    return {
        "content": response.content,
        "success": response.success,
        "token_usage": response.token_usage.to_dict(),
    }


def _execute_implement_service(
    parameters: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Execute service implementation.
    
    Args:
        parameters: Service parameters.
        context: Execution context.
        
    Returns:
        Implementation result.
    """
    from aurora_dev.agents.specialized.developers import BackendAgent
    
    agent = BackendAgent(project_id=context.get("project_id"))
    response = agent.implement_service(
        service_name=parameters.get("service_name", "Service"),
        methods=parameters.get("methods", []),
        dependencies=parameters.get("dependencies"),
        language=parameters.get("language", "python"),
    )
    
    return {
        "content": response.content,
        "success": response.success,
        "token_usage": response.token_usage.to_dict(),
    }


def _execute_generate_tests(
    parameters: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Execute test generation.
    
    Args:
        parameters: Test parameters.
        context: Execution context.
        
    Returns:
        Test generation result.
    """
    from aurora_dev.agents.specialized.quality import TestEngineerAgent
    
    agent = TestEngineerAgent(project_id=context.get("project_id"))
    response = agent.generate_unit_tests(
        code=parameters.get("code", ""),
        language=parameters.get("language", "python"),
        coverage_target=parameters.get("coverage_target", 0.8),
    )
    
    return {
        "content": response.content,
        "success": response.success,
        "token_usage": response.token_usage.to_dict(),
    }


def _execute_security_audit(
    parameters: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Execute security audit.
    
    Args:
        parameters: Audit parameters.
        context: Execution context.
        
    Returns:
        Audit result.
    """
    from aurora_dev.agents.specialized.quality import SecurityAuditorAgent
    
    agent = SecurityAuditorAgent(project_id=context.get("project_id"))
    response = agent.audit_code(
        code=parameters.get("code", ""),
        language=parameters.get("language", "python"),
        context=parameters.get("audit_context"),
    )
    
    return {
        "content": response.content,
        "success": response.success,
        "token_usage": response.token_usage.to_dict(),
    }


def _execute_code_review(
    parameters: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Execute code review.
    
    Args:
        parameters: Review parameters.
        context: Execution context.
        
    Returns:
        Review result.
    """
    from aurora_dev.agents.specialized.quality import CodeReviewerAgent
    
    agent = CodeReviewerAgent(project_id=context.get("project_id"))
    response = agent.review_code(
        code=parameters.get("code", ""),
        language=parameters.get("language", "python"),
        context=parameters.get("review_context"),
    )
    
    return {
        "content": response.content,
        "success": response.success,
        "token_usage": response.token_usage.to_dict(),
    }


def _execute_generic(
    operation: str,
    parameters: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Execute a generic operation.
    
    Args:
        operation: Operation name.
        parameters: Operation parameters.
        context: Execution context.
        
    Returns:
        Generic result placeholder.
    """
    logger.warning(f"Generic execution for operation: {operation}")
    return {
        "operation": operation,
        "parameters": parameters,
        "status": "executed",
        "note": "Generic execution - implement specific handler",
    }


def _aggregate_by_type(
    results: list[Any],
    aggregation_type: str,
) -> Any:
    """Aggregate results based on type.
    
    Args:
        results: List of results to aggregate.
        aggregation_type: Type of aggregation.
        
    Returns:
        Aggregated result.
    """
    if aggregation_type == "merge":
        merged = {}
        for result in results:
            if isinstance(result, dict):
                merged.update(result)
        return merged
    elif aggregation_type == "concat":
        return results
    elif aggregation_type == "sum":
        return sum(r for r in results if isinstance(r, (int, float)))
    else:
        return results


if __name__ == "__main__":
    payload = TaskPayload.from_dict({
        "metadata": {"task_id": "test-123"},
        "operation": "implement_endpoint",
        "parameters": {"endpoint": "/api/test", "method": "GET"},
        "context": {},
    })
    print(f"Test payload: {payload.to_dict()}")
