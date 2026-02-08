# Using the API

Programmatic control of your agents.

**Last Updated:** February 8, 2026
**Audience:** Integrators

> **Before Reading This**
>
> You should understand:
> - [REST API Reference](../07_api_reference/rest_api.md)
> - [Authentication](../07_api_reference/authentication.md)

## Why use the API?

The CLI is great for humans. The API is for machines.
You can use the API to:
- Trigger an agent from a GitHub Action.
- Build a custom GUI.
- Integrate AURORA-DEV into your Slack bot.

## Endpoint Structure

The API runs on port 8000 by default.

```bash
GET /api/v1/health
POST /api/v1/tasks
GET /api/v1/agents/{name}/status
```

## Authentication

All requests must include the `Authorization` header.
```bash
Authorization: Bearer <YOUR_API_KEY>
```
Generate specific keys in the CLI: `aurora auth create-key --name "CI System"`.

## WebSockets

For real-time updates (like seeing the agent type), connect to the WebSocket:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/events');
ws.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(log.message);
};
```

## Python Client

We provide a Python SDK for easier access.
```python
from aurora_client import Aurora

client = Aurora(params)
task = client.create_task("Fix bug #123")
task.wait_for_completion()
print(task.result)
```

## Related Reading

- [REST API Reference](../07_api_reference/rest_api.md)
- [Python SDK](../07_api_reference/python_sdk.md)
