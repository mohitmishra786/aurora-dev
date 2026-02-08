# Backup & Restore

Saving your bacon.

**Last Updated:** February 8, 2026
**Audience:** SysAdmins

> **Before Reading This**
>
> You should understand:
> - [Self Hosted](./self_hosted.md)
> - [Database Configuration](../13_configuration/database_configuration.md)

## What to Backup

1. **PostgreSQL:** The core relational data.
2. **Qdrant:** The vector embeddings. (Re-computable, but expensive).
3. **S3/MinIO:** Artifact files (PDFs, Diagrams).

## Automated Backups

We provide a script `scripts/backup.sh`.
It runs `pg_dump` and uploads to S3.
Add to crontab:
```bash
0 3 * * * /app/scripts/backup.sh
```

## Restoration Procedure

1. **Stop the App:** Prevent new writes.
2. **Restore DB:**
   ```bash
   pg_restore -d aurora latest.dump
   ```
3. **Restore Files:** Sync S3 bucket.
4. **Start App:** Verify integrity.

## Testing

Run a "Fire Drill" every quarter. Restore the backup to a staging server and run the test suite. A backup you haven't tested is not a backup.

## Related Reading

- [Disaster Recovery](./disaster_recovery.md)
- [Database Maintenance](../09_operations/database_maintenance.md)
