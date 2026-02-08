# REST API Reference

AURORA-DEV HTTP API documentation.

**Last Updated:** February 8, 2026  
**Audience:** Developers

## Base URL

```
https://api.aurora-dev.io/v1
```

## Authentication

```
Authorization: Bearer <token>
```

## Projects

### Create Project
```http
POST /projects
Content-Type: application/json

{
  "name": "my-app",
  "description": "Task management application",
  "template": "fullstack"
}
```

### Get Project
```http
GET /projects/{project_id}
```

### List Projects
```http
GET /projects?status=active&limit=10&offset=0
```

## Tasks

### Get Task Status
```http
GET /projects/{project_id}/tasks/{task_id}
```

### Retry Task
```http
POST /projects/{project_id}/tasks/{task_id}/retry
```

## Agents

### List Agent Status
```http
GET /agents
```

## Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Server Error |

## Related Reading

- [WebSocket API](./websocket_api.md)
