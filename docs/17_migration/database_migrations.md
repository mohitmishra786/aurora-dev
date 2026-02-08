# Database Migrations

Managing database schema changes.

**Last Updated:** February 8, 2026  
**Audience:** DevOps Engineers

## Running Migrations

```bash
# Apply all pending
alembic upgrade head

# Rollback one
alembic downgrade -1

# Check current
alembic current
```

## Creating Migrations

```bash
alembic revision --autogenerate -m "Add field"
```

## Best Practices

1. **Test migrations** in staging first
2. **Backup** before applying
3. **Monitor** during application
4. **Have rollback** ready

## Zero-Downtime

For production:
1. Add new column (nullable)
2. Deploy code that writes both
3. Backfill data
4. Make column required
5. Remove old code

## Related Reading

- [Database Agent](../03_agent_specifications/08_database_agent.md)
