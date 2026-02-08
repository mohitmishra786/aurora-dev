# Security Auditing

Who watches the watchmen?

**Last Updated:** February 8, 2026
**Audience:** Compliance Officers

> **Before Reading This**
>
> You should understand:
> - [Audit Trail](../11_compliance/audit_trail.md)
> - [Logging Setup](../09_operations/logging_setup.md)

## The Audit Log

Every write operation records an audit event.
- **Actor:** User ID or Service Account.
- **Action:** UPDATE, DELETE, CREATE.
- **Resource:** Entity ID.
- **Change:** Diff of the data (excluding secrets).

## Storage

Audit logs are stored in a separate, immutable database table `audit_events`.
They are also shipped to cold storage (S3 Glacier) for 7-year retention.

## Review Process

The `Security Auditor Agent` reviews the logs daily for anomalies (e.g., a user exporting 1000 records at 3 AM).

## Related Reading

- [Audit Trail](../11_compliance/audit_trail.md)
- [Incident Reporting](./incident_reporting.md)
