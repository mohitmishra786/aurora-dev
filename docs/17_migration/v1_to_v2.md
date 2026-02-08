# Migration from v1.x to v2.x

Upgrading to AURORA-DEV 2.0.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Breaking Changes

1. **Config format**: `aurora.yml` → `aurora.yaml`
2. **Agent names**: `BackendDeveloper` → `backend`
3. **Memory API**: New interface

## Migration Steps

### 1. Backup
```bash
pg_dump aurora_dev > backup.sql
```

### 2. Update Config
```bash
aurora migrate config
```

### 3. Update Database
```bash
aurora migrate database
```

### 4. Verify
```bash
aurora health check
```

## Config Changes

Old:
```yaml
agents:
  BackendDeveloper:
    model: claude-3-sonnet
```

New:
```yaml
agents:
  backend:
    model: claude-3-sonnet-20240229
```

## Related Reading

- [Changelog](../19_reference/changelog.md)
