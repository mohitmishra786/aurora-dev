# Agent APIs

Talking to the brains.

**Last Updated:** February 8, 2026
**Audience:** API Consumers

> **Before Reading This**
>
> You should understand:
> - [Agent Specifications](../03_agent_specifications/00_base_agent.md)
> - [REST API](./rest_api.md)

## List Agents

`GET /agents`

Returns all registered agents and their statuses.
```json
[
  {
    "id": "backend",
    "name": "Backend Engineer",
    "status": "idle",
    "capabilities": ["python", "sql"]
  }
]
```

## Run Agent

`POST /agents/{id}/run`

Directly invoke an agent. *Warning: detailed usage cost applies.*

Request:
```json
{
  "prompt": "Optimize this SQL query...",
  "context_files": ["src/db/queries.py"]
}
```

## Get Agent State

`GET /agents/{id}/memory`

Inspect the agent's short-term memory (conversation history).
Useful for debugging "Why did it say that?".

## Update Configuration

`PATCH /agents/{id}`

Dynamically adjust temperature or system prompt.
```json
{
  "temperature": 0.5,
  "system_prompt": "You are a pirate."
}
```

## Related Reading

- [Task API](./task_api.md)
- [Agent Configuration](../13_configuration/agent_configuration.md)
