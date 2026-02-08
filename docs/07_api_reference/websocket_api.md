# WebSocket API

Real-time events.

**Last Updated:** February 8, 2026
**Audience:** Frontend Developers

> **Before Reading This**
>
> You should understand:
> - [REST API](./rest_api.md)
> - [Notification System](../09_operations/alerting_rules.md)

## Connection

Connect to `wss://api.aurora.dev/v1/events`.
You must pass the token in the query param: `?token=YOUR_JWT`.

## Event Format

All messages follow the CloudEvents spec.

```json
{
  "specversion": "1.0",
  "type": "agent.thought",
  "source": "/agent/backend",
  "id": "A234-1234-1234",
  "time": "2026-02-08T10:00:00Z",
  "data": {
    "content": "I am reading the file now.",
    "task_id": "task_123"
  }
}
```

## Channels

### `/task/{id}`
Subscribe to updates for a specific task.
Events: `task.updated`, `task.completed`, `agent.log`.

### `/system/status`
Subscribe to system health.
Events: `system.cpu_high`, `system.api_outage`.

## Heartbeat

Send `{"type": "ping"}` every 30 seconds to keep the connection alive. Server responds with `{"type": "pong"}`.

## Related Reading

- [REST API](./rest_api.md)
- [Monitoring API](./monitoring_api.md)
