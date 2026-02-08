# Error Codes

What went wrong.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [REST API](./rest_api.md)
> - [Troubleshooting](../14_troubleshooting/common_errors.md)

## Format

Errors always include a machine-readable `code`.

## Common Codes

### General
- `invalid_request`: Bad JSON or missing fields.
- `unauthorized`: Missing API Key.
- `forbidden`: API Key lacks scope.

### Tasks
- `task_not_found`: ID incorrect.
- `task_locked`: Cannot edit while agent is running.
- `dependency_cycle`: Task loop detected.

### Agents
- `agent_busy`: No capacity in worker pool.
- `context_length_exceeded`: Files too big for model.
- `llm_error`: Example: OpenAI 500 error.

## Debugging

Every error includes a `request_id`.
Copy this ID and search the logs:
```bash
aurora logs --grep "req_abc123"
```

## Related Reading

- [Troubleshooting](../14_troubleshooting/common_errors.md)
- [REST API](./rest_api.md)
