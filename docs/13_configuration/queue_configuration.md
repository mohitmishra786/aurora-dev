# Queue Configuration

Traffic control.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Scaling Guide](../08_deployment/scaling_guide.md)
> - [Redis Operations](../09_operations/redis_operations.md)

## Celery Settings

We use Celery for background processing.

- **Broker:** Redis (`redis://localhost:6379/0`)
- **Backend:** Redis (`redis://localhost:6379/1`)

## Queues

We split work into queues to prioritize traffic.

1. `high_priority`: Interactive user tasks.
2. `default`: Standard logic.
3. `low_priority`: Monthly reporting, batch emails.

## Concurrency

Per worker node:
`CELERY_CONCURRENCY=4`
Increase this if your tasks are I/O bound (waiting on API calls).
Decrease if CPU bound.

## Retry Policy

Default: 3 retries, exponential backoff.
Max delay: 60 seconds.
Dead Letter Queue (DLQ): Failed tasks move here for manual inspection.

## Related Reading

- [Redis Operations](../09_operations/redis_operations.md)
- [Performance Tuning](../06_developer_guides/performance_tuning.md)
