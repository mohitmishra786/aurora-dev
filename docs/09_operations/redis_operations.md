# Redis Operations

More than just a cache.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Caching Strategies](../16_performance/caching_strategies.md)
> - [Redis Issues](../14_troubleshooting/redis_issues.md)

## Eviction Policy

When Redis fills up, what dies?
Set `maxmemory-policy allkeys-lru`.
This deletes the least used keys to make room for new ones.
If you use Redis for Queues (Celery), use `volatile-lru` to protect non-expiring keys.

## Persistence

Do you need RDB or AOF?
- **RDB (Snapshots):** Good for backups.
- **AOF (Append Only File):** Good for durability.
For caching: RDB is fine.
For job queues: AOF every second (`appendfsync everysec`).

## Clustering

If memory > 64GB, use Redis Cluster.
Note: Multi-key operations (`MGET`) are limited in Cluster mode if keys are on different nodes.

## Related Reading

- [Caching Strategies](../16_performance/caching_strategies.md)
- [Database Maintenance](./database_maintenance.md)
