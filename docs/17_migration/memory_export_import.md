# Memory Export/Import

Moving memory between instances.

**Last Updated:** February 8, 2026  
**Audience:** DevOps Engineers

## Export Memory

```bash
aurora memory export --output memory_backup.json
```

Options:
- `--project <id>` - Specific project
- `--tier working,long_term` - Specific tiers
- `--since 2024-01-01` - Date filter

## Import Memory

```bash
aurora memory import memory_backup.json
```

Options:
- `--merge` - Merge with existing
- `--replace` - Replace existing

## Format

```json
{
  "version": "2.0",
  "exported_at": "2024-02-08T10:00:00Z",
  "items": [
    {
      "id": "mem-123",
      "content": "Use bcrypt for passwords",
      "tier": "long_term",
      "tags": ["security"]
    }
  ]
}
```

## Related Reading

- [Memory Architecture](../02_architecture/memory_architecture.md)
