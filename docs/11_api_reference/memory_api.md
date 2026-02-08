# Memory API

Programmatic memory system access.

**Last Updated:** February 8, 2026  
**Audience:** Developers

## Store Pattern

```python
from aurora_dev.memory import MemoryCoordinator

memory = MemoryCoordinator()

await memory.store_pattern(
    content="Use bcrypt for password hashing",
    tags=["security", "authentication"],
    project_id="proj-123"
)
```

## Search Memory

```python
results = await memory.get_context(
    query="JWT implementation",
    project_id="proj-123",
    limit=5
)
```

## Store Reflexion

```python
await memory.store_reflexion(
    task_id="task-456",
    original_approach="Plain text passwords",
    failure_reason="Security scan failed",
    improved_approach="Use bcrypt with cost=12",
    tags=["security"]
)
```

## Promote to Long-term

```python
await memory.promote_to_long_term(memory_id="mem-789")
```

## Related Reading

- [Memory Architecture](../02_architecture/memory_architecture.md)
