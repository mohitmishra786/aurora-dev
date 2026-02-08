# Custom Agent Development

Building a better brain.

**Last Updated:** February 8, 2026
**Audience:** Python Developers

> **Before Reading This**
>
> You should understand:
> - [Agent Specifications](../03_agent_specifications/00_base_agent.md)
> - [Adding Agents](../06_developer_guides/adding_agents.md)

## The Lifecycle

1. **Plan:** The agent receives a task and breaks it down.
2. **Thought:** The LLM generates a reasoning trace.
3. **Action:** The agent calls a tool (e.g., `read_file`).
4. **Observation:** The tool returns output.
5. **Reflexion:** The agent critiques its own action.

## Overriding the Loop

You can subclass `BaseAgent` to change this behavior.

```python
class FastAgent(BaseAgent):
    async def run_step(self, task):
        # Skip planning, just execute
        action = await self.llm.predict(task)
        return await self.execute(action)
```

## Custom Tools

Tools are Pydantic models with a `run` method.
```python
class SearchWeb(Tool):
    query: str
    
    def run(self):
        return google.search(self.query)
```

## Related Reading

- [Plugin Architecture](./plugin_architecture.md)
- [Agent Swarms](./agent_swarms.md)
