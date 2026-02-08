# Multi-Tenancy

One codebase, many customers.

**Last Updated:** February 8, 2026
**Audience:** Architects

> **Before Reading This**
>
> You should understand:
> - [Database Configuration](./database_configuration.md)
> - [Security Model](../10_security/security_model.md)

## Approach: Row-Level Security (Recommended)

Every table has a `tenant_id` column.
Postgres RLS policies enforce isolation.
```sql
CREATE POLICY tenant_isolation ON task
USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

## Approach: Schema per Tenant

Each customer gets a separate Postgres Schema.
Better isolation, harder migration.

## Data Leakage Prevention

The `middleware` sets the `tenant_id` on every request context.
If a developer forgets to filter by tenant, the DB policy blocks the query.

## Related Reading

- [Database Configuration](./database_configuration.md)
- [Security Model](../10_security/security_model.md)
