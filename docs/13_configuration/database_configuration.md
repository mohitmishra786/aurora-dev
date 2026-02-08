# Database Configuration

The heart of the system.

**Last Updated:** February 8, 2026
**Audience:** DBAs

> **Before Reading This**
>
> You should understand:
> - [Database Maintenance](../09_operations/database_maintenance.md)
> - [Environment Variables](./environment_variables.md)

## Connection String

`postgres://user:pass@host:5432/dbname?sslmode=require`

## SQLAlchemy Settings

- **Pool Size:** 20 (Keep connections open).
- **Max Overflow:** 10 (Allow bursts).
- **Pool Timeout:** 30s.

## Migrations

We use **Alembic**.
`alembic.ini` configuration:
```ini
[alembic]
script_location = migrations
prepend_sys_path = .
```

To auto-generate a migration:
`aurora db revision --autogenerate -m "Add user table"`

## Read Replicas

Configure `DB_READ_HOST` to enable splitting read/write traffic.
The application middleware automatically routes `GET` requests to the read replica.

## Related Reading

- [Database Maintenance](../09_operations/database_maintenance.md)
- [Environment Variables](./environment_variables.md)
