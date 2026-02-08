# Agent API

Programmatic agent interaction.

**Last Updated:** February 8, 2026  
**Audience:** Developers

## Creating Agents

```python
from aurora_dev.agents import BackendAgent

agent = BackendAgent(
    model="claude-3-sonnet-20240229",
    project_id="proj-123"
)
```

## Execute Task

```python
from aurora_dev.core import Task

task = Task(
    title="Create user endpoint",
    description="POST /api/users",
    acceptance_criteria=["Creates user", "Returns 201"]
)

result = await agent.execute(task)
```

## Chat Interface

```python
response = await agent.chat(
    "How should I implement JWT refresh tokens?"
)
```

## Memory Access

```python
patterns = await agent.memory.search(
    query="authentication patterns",
    limit=5
)
```

## Related Reading

- [Base Agent](../03_agent_specifications/00_base_agent.md)
