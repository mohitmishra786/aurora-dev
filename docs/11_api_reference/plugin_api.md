# Plugin API

Extending AURORA-DEV with plugins.

**Last Updated:** February 8, 2026  
**Audience:** Developers

## Plugin Interface

```python
from aurora_dev.plugins import Plugin, hook

class MyPlugin(Plugin):
    name = "my-plugin"
    version = "1.0.0"
    
    @hook("project_created")
    async def on_project_created(self, project):
        pass
```

## Available Hooks

| Hook | Args | Description |
|------|------|-------------|
| `project_created` | project | New project |
| `task_assigned` | task, agent | Task assigned |
| `task_completed` | task, result | Task done |
| `agent_error` | agent, error | Error occurred |
| `project_completed` | project | Project done |

## Context Access

```python
@hook("task_completed")
async def on_task_completed(self, task, result):
    # Access memory
    patterns = await self.memory.search("auth patterns")
    
    # Access config
    api_key = self.config.get("my_api_key")
```

## Related Reading

- [Plugin Development](../06_developer_guides/plugin_development.md)
