# Disaster Recovery

When the data center burns down.

**Last Updated:** February 8, 2026
**Audience:** CTOs, SREs

> **Before Reading This**
>
> You should understand:
> - [Backup & Restore](./backup_restore.md)
> - [Multi-Region](../17_advanced_topics/multi_region.md)

## RTO and RPO

- **RTO (Recovery Time Objective):** < 4 hours. How long to get back online.
- **RPO (Recovery Point Objective):** < 15 minutes. How much data we lose.

## Strategy: Cold Standby

1. Replicate Database WAL logs to a secondary region (e.g., us-east-1 -> us-west-2).
2. Keep a Terraform script ready to spin up compute in us-west-2.
3. In an event, flip the DNS switch (Route53) to the new region.

## Strategy: Active-Active (Advanced)

Run full stacks in both regions. Use `pg_bdr` (Bi-Directional Replication) or CockroachDB.
This is complex and expensive but offers RTO < 1 minute.

## Communication Plan

Who calls whom?
1. Alert PagerDuty (DevOps).
2. Update Status Page (Public).
3. Email Customers (Support).

## Related Reading

- [Backup & Restore](./backup_restore.md)
- [Runbook Template](../22_templates/runbook_template.md)
