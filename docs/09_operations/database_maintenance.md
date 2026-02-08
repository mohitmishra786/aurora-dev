# Database Maintenance

The care and feeding of Postgres.

**Last Updated:** February 8, 2026
**Audience:** DBAs

> **Before Reading This**
>
> You should understand:
> - [Database Configuration](../13_configuration/database_configuration.md)
> - [Backup & Restore](../08_deployment/backup_restore.md)

## Vacuuming

Postgres uses MVCC. Deleted rows are just marked "dead." They still take space.
Autovacuum should be on.
Monitor `n_dead_tup` metrics. If bloat > 20%, manual `VACUUM FULL` may be needed (locks table!).

## Index Maintenance

Indexes fragment over time.
Run `REINDEX CONCURRENTLY` periodically on high-churn tables.

## Connection Pooling

Postgres connections are expensive (process-based).
Use `pgbouncer` in transaction pooling mode.
Max connections on DB side: 500.
Max connections on App side: 5000 (handled by pgbouncer).

## Related Reading

- [Database Configuration](../13_configuration/database_configuration.md)
- [Redis Operations](./redis_operations.md)
