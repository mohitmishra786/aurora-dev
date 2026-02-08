# Plugin Architecture

Extensible by design.

**Last Updated:** February 8, 2026
**Audience:** Architects

> **Before Reading This**
>
> You should understand:
> - [Creating Plugins](../06_developer_guides/creating_plugins.md)
> - [Plugin Architecture Diagram](../21_diagrams/architecture/plugin_architecture.mmd)

## The Hook System

We use `pluggy` (same as pytest).
Hooks allow plugins to intercept events.

- `aurora_setup`: Called on startup.
- `aurora_task_start`: Called before task execution.
- `aurora_llm_request`: Called before sending prompt to OpenAI.

## Example: Audit Plugin

```python
@aurora_hook
def aurora_llm_request(prompt):
    logging.info(f"Sending prompt: {len(prompt)} chars")
```

## Component Registration

Plugins can register:
- **Agents:** `registry.register_agent("sql", SQLAgent)`
- **Tools:** `registry.register_tool("aws", AWSTool)`
- **Memories:** `registry.register_memory("redis", RedisMemory)`

## Related Reading

- [Creating Plugins](../06_developer_guides/creating_plugins.md)
- [Custom Workflows](./custom_workflows.md)
