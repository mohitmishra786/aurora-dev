# Audit Trail

The timeline of truth.

**Last Updated:** February 8, 2026
**Audience:** Security Auditors

> **Before Reading This**
>
> You should understand:
> - [Security Auditing](../10_security/security_auditing.md)
> - [Logging Setup](../09_operations/logging_setup.md)

## Schema

The `audit_events` table captures:

```sql
CREATE TABLE audit_events (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP,
    actor_id STRING,
    event_type STRING,
    resource_id STRING,
    old_value JSONB,
    new_value JSONB,
    ip_address STRING
);
```

## Immutability

This table is "Append Only".
We revoke `UPDATE` and `DELETE` permissions from the application user.
Only the `admin` role can truncate distinct partitions for archiving.

## Exporting

Customers can export their own audit logs via the Dashboard settings page (CSV/JSON).

## Related Reading

- [Security Auditing](../10_security/security_auditing.md)
- [SOC2 Compliance](./soc2_compliance.md)
