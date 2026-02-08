# Task API

Managing work.

**Last Updated:** February 8, 2026
**Audience:** Project Managers

> **Before Reading This**
>
> You should understand:
> - [Task Decomposition](../04_core_concepts/task_decomposition.md)
> - [REST API](./rest_api.md)

## Create Task

`POST /tasks`

Request:
```json
{
  "title": "Implement Dark Mode",
  "description": "Add CSS variables for...",
  "parent_id": null
}
```

Response:
```json
{
  "id": "task_123",
  "status": "planning"
}
```

## Get Task Graph

`GET /tasks/graph`

Returns the dependency tree (DAG).

```json
{
  "nodes": [{"id": "task_1", "label": "UI"}, {"id": "task_2", "label": "API"}],
  "edges": [{"from": "task_2", "to": "task_1", "type": "hard"}]
}
```

## Cancel Task

`POST /tasks/{id}/cancel`

Stops execution immediately. Any running agents are killed.

## Approve Task

`POST /tasks/{id}/approve`

If the task is in `waiting_approval` state (due to a Quality Gate), this endpoint moves it to `done`.

## Related Reading

- [Agent APIs](./agent_apis.md)
- [Quality Gates](../04_core_concepts/quality_gates.md)
