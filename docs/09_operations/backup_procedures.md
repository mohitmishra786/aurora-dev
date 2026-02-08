# Backup Procedures

Data backup and recovery for AURORA-DEV.

**Last Updated:** February 8, 2026  
**Audience:** DevOps Engineers

## What to Backup

| Component | Method | Frequency |
|-----------|--------|-----------|
| PostgreSQL | pg_dump | Daily |
| Redis | RDB/AOF | Hourly |
| Git repos | Mirror | Real-time |
| Configs | Version control | On change |

## PostgreSQL Backup

```bash
# Backup
pg_dump -h localhost -U aurora aurora_dev > backup.sql

# Restore
psql -h localhost -U aurora aurora_dev < backup.sql
```

## Redis Backup

```bash
# Trigger RDB save
redis-cli BGSAVE

# Copy snapshot
cp /var/lib/redis/dump.rdb /backups/
```

## Automated Backup Script

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -h db aurora_dev | gzip > /backups/db_$DATE.sql.gz
redis-cli -h redis BGSAVE
aws s3 sync /backups s3://aurora-backups/
```

## Related Reading

- [Disaster Recovery](./disaster_recovery.md)
