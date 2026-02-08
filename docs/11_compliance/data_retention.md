# Data Retention Policy

How long we keep stuff.

**Last Updated:** February 8, 2026
**Audience:** DBAs, Legal

> **Before Reading This**
>
> You should understand:
> - [Backup & Restore](../08_deployment/backup_restore.md)
> - [GDPR Compliance](./gdpr_compliance.md)

## Schedule

| Data Type | Retention Period | Rationale |
|-----------|------------------|-----------|
| Application Logs | 30 Days | Debugging |
| Security Logs | 1 Year | Auditing |
| User Accounts | Life of Account + 30 days | Grace period |
| Billing Records | 7 Years | Tax Law |
| Backups | 90 Days | Disaster Recovery |

## Automated Pruning

We run a cron job `scripts/prune_data.py` every Sunday.
It executes `DELETE FROM logs WHERE created_at < NOW() - INTERVAL '30 days'`.

## Legal Holds

If a customer is involved in litigation, we can flag their account to suspend deletion.

## Related Reading

- [Right to Erasure](./right_to_erasure.md)
- [Backup & Restore](../08_deployment/backup_restore.md)
