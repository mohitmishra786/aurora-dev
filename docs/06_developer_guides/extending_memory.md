# Extending Memory

Giving the elephant more storage.

**Last Updated:** February 8, 2026
**Audience:** Backend Developers

> **Before Reading This**
>
> You should understand:
> - [Memory Architecture](../02_architecture/memory_architecture.md)
> - [Memory Configuration](../13_configuration/memory_configuration.md)

## The Memory Interface

All memory backends implement the `MemoryStore` interface.

```python
class MemoryStore(ABC):
    @abstractmethod
    def add(self, text: str, meta: dict): ...
    
    @abstractmethod
    def search(self, query: str) -> List[Result]: ...
```

## Adding a New Backend

To support `Pinecone`, `Weaviate`, or `Postgres (pgvector)`, simply implement this class.

### 1. Create the Class
```python
class PineconeStore(MemoryStore):
    def __init__(self, api_key):
        self.index = pinecone.Index("aurora")
    
    def add(self, text, meta):
        vec = openai.embed(text)
        self.index.upsert(vec, meta)
```

### 2. Register it
```python
from aurora.memory import registry
registry.register("pinecone", PineconeStore)
```

### 3. Configure it
```yaml
memory:
  backend: pinecone
  pinecone:
    api_key: ${PINECONE_KEY}
```

## Optimizing Retrieval

Memory is only useful if you can find it.
- **Hybrid Search:** Combine Keyword (BM25) + Vector (Cosine). This finds specific variable names *and* semantic concepts.
- **Reranking:** Use a Cross-Encoder (Cohere/BGE) to re-rank the top 100 vector results for better accuracy.

## Related Reading

- [Memory Architecture](../02_architecture/memory_architecture.md)
- [Context Optimization](../23_research/context_optimization.md)
