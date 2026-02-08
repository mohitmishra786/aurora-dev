# Redis Issues

Cache miss loops.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Redis Operations](../09_operations/redis_operations.md)
> - [Queue Configuration](../13_configuration/queue_configuration.md)

## Connection Refused

*Cause:* Redis is bound to 127.0.0.1 but you are calling from another container.
*Fix:* Bind to 0.0.0.0 or use Docker network aliases.

## OOM (Out of Memory)

*Cause:* Cache keys never expire.
*Fix:* Set a default TTL (Time To Live). Set `maxmemory` limit.

## Thundering Herd

*Cause:* Cache key expires, 1000 users hit DB at once.
*Fix:* Implement "Cache Stampede Protection" (locking or probability-based early expiration).

## Related Reading

- [Redis Operations](../09_operations/redis_operations.md)
- [Performance Problems](./performance_problems.md)
