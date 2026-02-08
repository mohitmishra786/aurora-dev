# Python SDK

The pythonic way.

**Last Updated:** February 8, 2026
**Audience:** Python Developers

> **Before Reading This**
>
> You should understand:
> - [REST API](./rest_api.md)
> - [Installation](../01_getting_started/installation.md)

## Installation

```bash
pip install aurora-sdk
```

## Initialization

```python
from aurora import AuroraClient

client = AuroraClient(api_key="sk_...")
```

## Agents

Interact with agents directly.

```python
# Synchronous
response = client.agents.run("backend", "Fix the bug")
print(response)

# Asynchronous
async def main():
    stream = await client.agents.run_stream("backend", "Refactor X")
    async for chunk in stream:
        print(chunk.text, end="")
```

## Memory

Manage the knowledge base.

```python
# Add document
client.memory.add(
    collection="docs",
    text="The API uses port 8000",
    metadata={"source": "readme"}
)

# Search
results = client.memory.search("port", limit=5)
```

## Error Handling

The SDK raises specific exceptions.

```python
from aurora.errors import RateLimitError, APIError

try:
    client.tasks.create(...)
except RateLimitError:
    print("Slow down!")
```

## Related Reading

- [REST API](./rest_api.md)
- [Agent APIs](./agent_apis.md)
