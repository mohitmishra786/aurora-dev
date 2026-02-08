# Log Management

Centralized logging for AURORA-DEV.

**Last Updated:** February 8, 2026  
**Audience:** DevOps Engineers

## Log Format

```json
{
  "timestamp": "2024-02-08T10:30:15Z",
  "level": "INFO",
  "agent": "backend",
  "task_id": "task-123",
  "message": "Task completed",
  "duration_ms": 45000
}
```

## ELK Stack Setup

```yaml
# filebeat.yml
filebeat.inputs:
  - type: container
    paths:
      - /var/lib/docker/containers/*/*.log
    
output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

## Log Levels

| Level | Use Case |
|-------|----------|
| ERROR | Failures requiring attention |
| WARN | Concerning but handled |
| INFO | Normal operations |
| DEBUG | Troubleshooting |

## Retention

| Type | Retention |
|------|-----------|
| ERROR | 90 days |
| WARN | 30 days |
| INFO | 14 days |
| DEBUG | 3 days |

## Related Reading

- [Debugging Tips](../06_developer_guides/debugging_tips.md)
