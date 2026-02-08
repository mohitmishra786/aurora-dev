# Database Issues

Deadlocks and timeouts.

**Last Updated:** February 8, 2026
**Audience:** DBAs

> **Before Reading This**
>
> You should understand:
> - [Database Maintenance](../09_operations/database_maintenance.md)
> - [Database Configuration](../13_configuration/database_configuration.md)

## Deadlocks

*Error:* `Deadlock found when trying to get lock`.
*Cause:* Two transactions modifying `Task` and `Agent` in reverse order.
*Fix:* Always sort lock acquisition order (e.g., sort IDs).

## Connection Leaks

*Error:* `FATAL: remaining connection slots are reserved for non-replication superuser roles`.
*Cause:* App not returning connections to pool.
*Fix:* Use context managers `async with get_db() as db:` to ensure automatic cleanup.

## Slow Queries

*Diagnosis:* Enable `log_min_duration_statement = 500ms` in Postgres.
*Fix:* Add missing index. `CREATE INDEX ON task (status);`.

## Related Reading

- [Database Maintenance](../09_operations/database_maintenance.md)
- [Monitoring Setup](../09_operations/monitoring_setup.md)
