# Plugin Development

Creating plugins to extend AURORA-DEV functionality.

**Last Updated:** February 8, 2026  
**Audience:** Developers

## Plugin Structure

```
aurora-plugin-example/
├── pyproject.toml
├── aurora_plugin_example/
│   ├── __init__.py
│   └── plugin.py
└── tests/
```

## Plugin Interface

```python
from aurora_dev.plugins import Plugin, hook

class ExamplePlugin(Plugin):
    name = "example"
    version = "1.0.0"
    
    @hook("project_created")
    async def on_project_created(self, project: Project):
        """Called when a new project is created."""
        pass
    
    @hook("task_completed")
    async def on_task_completed(self, task: Task):
        """Called when a task completes."""
        pass
```

## Available Hooks

| Hook | Trigger |
|------|---------|
| `project_created` | New project initialized |
| `phase_started` | Workflow phase begins |
| `task_assigned` | Task assigned to agent |
| `task_completed` | Task finished |
| `agent_error` | Agent encounters error |
| `project_completed` | Project finishes |

## Installation

```bash
pip install aurora-plugin-example
```

```yaml
# aurora.yaml
plugins:
  - aurora-plugin-example
```

## Related Reading

- [Plugin API](../11_api_reference/plugin_api.md)
