# Memory Extension

Extending and customizing the memory system.

**Last Updated:** February 8, 2026  
**Audience:** Developers

## Custom Memory Types

```python
class MemoryType(Enum):
    PATTERN = "pattern"
    REFLEXION = "reflexion"
    DECISION = "decision"
    CONFLICT = "conflict"
    CUSTOM = "custom"  # Add your type
```

## Custom Memory Store

```python
class CustomStore:
    async def store(self, item: MemoryItem) -> str:
        # Custom storage logic
        return item_id
    
    async def search(self, query: str, limit: int) -> list[MemoryItem]:
        # Custom search logic
        return results
```

## Registration

```python
memory_coordinator.register_store(
    tier="custom",
    store=CustomStore()
)
```

## Custom Promotion Logic

```python
class CustomPromotionPolicy:
    def should_promote(self, item: MemoryItem) -> bool:
        return (
            item.access_count > 10 and
            item.success_rate > 0.9
        )
```

## Related Reading

- [Memory Architecture](../02_architecture/memory_architecture.md)
- [Memory Coordinator](../03_agent_specifications/02_memory_coordinator.md)
