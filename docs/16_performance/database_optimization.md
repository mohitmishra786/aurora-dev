# Database Optimization

Indexing 101.

**Last Updated:** February 8, 2026
**Audience:** DBAs

> **Before Reading This**
>
> You should understand:
> - [Optimization Techniques](./optimization_techniques.md)
> - [Database Issues](../14_troubleshooting/database_issues.md)

## Indexes

- **B-Tree:** Default. Good for equality and range.
- **GIN:** Good for JSONB and Full Text Search.
- **GiST:** Good for Geometry (PostGIS).

## Query Planning

Use `EXPLAIN ANALYZE` to see what Postgres is actually doing.
Look for `Seq Scan` on large tables -> usually means missing index.

## Partitioning

Split huge tables (e.g., Logs) by time. `logs_2026_01`, `logs_2026_02`.
Allows dropping old data instanty (`DROP TABLE`).

## Related Reading

- [Database Maintenance](../09_operations/database_maintenance.md)
- [Monitoring Setup](../09_operations/monitoring_setup.md)
