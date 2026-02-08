# Disaster Recovery

Recovery procedures for AURORA-DEV.

**Last Updated:** February 8, 2026  
**Audience:** DevOps Engineers

## Recovery Objectives

| Metric | Target |
|--------|--------|
| RTO (Recovery Time) | < 4 hours |
| RPO (Data Loss) | < 1 hour |

## Recovery Steps

### 1. Assess Damage
```bash
aurora status --health
kubectl get pods -n aurora
```

### 2. Restore Database
```bash
psql -h db aurora_dev < /backups/latest.sql
```

### 3. Restore Redis
```bash
redis-cli -h redis SHUTDOWN NOSAVE
cp /backups/dump.rdb /var/lib/redis/
redis-server
```

### 4. Verify Services
```bash
aurora health check
```

## Runbook Checklist

- [ ] Identify failure scope
- [ ] Notify stakeholders
- [ ] Restore from backup
- [ ] Verify data integrity
- [ ] Resume operations
- [ ] Post-mortem

## Related Reading

- [Backup Procedures](./backup_procedures.md)
