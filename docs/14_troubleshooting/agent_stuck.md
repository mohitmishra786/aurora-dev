# Agent Stuck Issues

Resolving stuck or unresponsive agents.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Symptoms

- Task not progressing for > 30 minutes
- Agent shows "running" but no output
- Timeout errors

## Diagnosis

```bash
# Check task status
aurora status --tasks

# View agent logs
aurora logs -a backend
```

## Solutions

### 1. Retry Task
```bash
aurora task retry <task-id>
```

### 2. Restart Agent
```bash
aurora agent restart <agent-name>
```

### 3. Check External Dependencies
- Is the API responding?
- Is the database accessible?
- Are there network issues?

### 4. Reduce Complexity
Split complex tasks into smaller pieces.

## Related Reading

- [Runbook Templates](../09_operations/runbook_templates.md)
