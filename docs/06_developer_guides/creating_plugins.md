# Creating Plugins

Extending the brain.

**Last Updated:** February 8, 2026
**Audience:** Plugin Developers

> **Before Reading This**
>
> You should understand:
> - [Plugin Architecture](../17_advanced_topics/plugin_architecture.md)
> - [Agent Template](../22_templates/agent_template.md)

## What is a Plugin?

A plugin is a Python package that adds:
1. **New Agents:** e.g., `UnityDeveloperAgent`.
2. **New Tools:** e.g., `SlackMessageTool`.
3. **New Memories:** e.g., `PineconeMemoryStore`.

## The Plugin Structure

```python
# my_plugin/__init__.py
from aurora.core.plugin import AuroraPlugin

class MyPlugin(AuroraPlugin):
    name = "discord-bot"
    version = "0.1.0"
    
    def register_agents(self, registry):
        from .agent import DiscordAgent
        registry.register("discord", DiscordAgent)
        
    def register_tools(self, registry):
        from .tools import SendMessage
        registry.register("send_discord", SendMessage)
```

## Installing Plugins

Users install plugins via pip:
```bash
pip install aurora-plugin-discord
```
Then enable them in `aurora.yaml`:
```yaml
plugins:
  - discord-bot
```

## Packaging

We use `poetry` for packaging.
```bash
poetry new aurora-plugin-discord
```
Ensure dependencies are correct. Do not pin `aurora-core` too strictly to avoid version conflicts.

## Testing Plugins

Use the `PluginTestHarness` to load your plugin in isolation.
```python
def test_plugin_load():
    harness = PluginTestHarness(MyPlugin)
    assert "discord" in harness.agent_registry
```

## Related Reading

- [Plugin Architecture](../17_advanced_topics/plugin_architecture.md)
- [Agent Template](../22_templates/agent_template.md)
