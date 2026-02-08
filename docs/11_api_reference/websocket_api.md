# WebSocket API

Real-time updates via WebSocket.

**Last Updated:** February 8, 2026  
**Audience:** Developers

## Connection

```javascript
const ws = new WebSocket('wss://api.aurora-dev.io/v1/ws');
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your-jwt-token'
}));
```

## Events

### Subscribe to Project
```json
{"type": "subscribe", "project_id": "proj-123"}
```

### Event Types

| Event | Description |
|-------|-------------|
| `task.started` | Task began execution |
| `task.completed` | Task finished |
| `task.failed` | Task failed |
| `agent.message` | Agent log message |
| `project.phase` | Phase changed |

### Event Payload
```json
{
  "type": "task.completed",
  "project_id": "proj-123",
  "task_id": "task-456",
  "data": {
    "duration_ms": 45000,
    "tokens_used": 2500
  },
  "timestamp": "2024-02-08T10:30:15Z"
}
```

## Related Reading

- [REST API](./rest_api.md)
