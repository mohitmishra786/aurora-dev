# Scaling Guide

From 1 user to 1 million.

**Last Updated:** February 8, 2026
**Audience:** Architects

> **Before Reading This**
>
> You should understand:
> - [Performance Monitoring](../09_operations/performance_monitoring.md)
> - [Caching Strategies](../16_performance/caching_strategies.md)

## Vertical Scaling (Easy)

Throw money at the problem. Upgrade RDS from `db.m5.large` to `db.m5.xlarge`.
Limit: ~500 concurrent users.

## Horizontal Scaling (Hard)

### 1. Stateless API
The `aurora-server` container is stateless. Simply run 10 copies behind a Load Balancer.

### 2. Database Read Replicas
Offload all `SELECT` queries to Read Replicas.
Set `DB_READ_HOST` in config.

### 3. Asynchronous Workers
Move heavy tasks (like Code Generation) to a background queue.
Use Celery with Redis Broker. Scale workers based on Queue Depth.

## Sharding

If you reach TB-scale data, you may need to shard the `events` table by `project_id`. This is natively supported by Citus (Postgres extension).

## Related Reading

- [Performance Monitoring](../09_operations/performance_monitoring.md)
- [Database Optimization](../16_performance/database_optimization.md)
