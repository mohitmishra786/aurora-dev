# Adding Agents

Expanding the workforce.

**Last Updated:** February 8, 2026
**Audience:** Plugin Developers

> **Before Reading This**
>
> You should understand:
> - [Agent Specifications](../03_agent_specifications/00_base_agent.md)
> - [Agent Configuration](../13_configuration/agent_configuration.md)

## The Agent Interface

All agents inherit from `BaseAgent`.

```python
from aurora.core.agent import BaseAgent

class MyNewAgent(BaseAgent):
    name = "my_new_agent"
    description = "Does cool stuff."
    
    async def run(self, task: Task) -> str:
        # Your logic here
        return "Done"
```

## Registration

You must register the agent in the `AgentRegistry` so the `Maestro` knows it exists.

```python
from aurora.core.registry import register_agent

register_agent(MyNewAgent)
```

## defining Capabilities

The `Maestro` uses semantic matching to assign tasks. You must provide a rich description.

```python
description = """
Specializes in generating Unity3D C# scripts.
Understands GameObjects, Monobehaviours, and Physics.
"""
```

## Adding Tools

Agents are useless without tools.

```python
self.tools = [
    RunUnityCompiler(),
    ReadAssetFile()
]
```

## Testing

Write a test case that mocks the LLM to verify the agent's logic flow.

```python
def test_agent_logic():
    agent = MyNewAgent(llm=MockLLM())
    result = agent.run("build game")
    assert result == "Done"
```

## Related Reading

- [Creating Plugins](./creating_plugins.md)
- [Agent Configuration](../13_configuration/agent_configuration.md)
