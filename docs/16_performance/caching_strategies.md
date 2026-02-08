# Caching Strategies

Remembering the past.

**Last Updated:** February 8, 2026
**Audience:** Architects

> **Before Reading This**
>
> You should understand:
> - [Redis Operations](../09_operations/redis_operations.md)
> - [Memory Configuration](../13_configuration/memory_configuration.md)

## Layers of Cache

1. **Browser Cache:** `Cache-Control: max-age=3600`. CDN edges.
2. **Application Cache:** In-memory `lru_cache` for static config.
3. **Distributed Cache:** Redis for shared state (Sessions, API responses).
4. **Database Cache:** Buffer Cache (internal to Postgres).

## Patterns

- **Cache-Aside:** Application checks Redis -> miss -> DB -> update Redis.
- **Write-Through:** Update DB and Redis simultaneously. (Simpler, but slower writes).

## Invalidation

"There are only two hard things in CS..."
We use **Time-based Expiration** (TTL) as a safety net.
For critical data, we manually invalidate keys on update: `redis.delete(f"user:{user_id}")`.

## Related Reading

- [Redis Operations](../09_operations/redis_operations.md)
- [Database Optimization](./database_optimization.md)
