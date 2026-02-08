# Memory Configuration

Tuning the hippocampus.

**Last Updated:** February 8, 2026
**Audience:** Backend Developers

> **Before Reading This**
>
> You should understand:
> - [Memory Architecture](../02_architecture/memory_architecture.md)
> - [Extending Memory](../06_developer_guides/extending_memory.md)

## Vector Store Settings

```yaml
memory:
  backend: qdrant
  collection_name: auroradev
  dimension: 1536  # OpenAI ada-002
  metric: cosine
```

## Embedding Models

We default to `text-embedding-3-small`.
You can switch to `cohere-embed-v3` for better multilingual support.
Or use `all-MiniLM-L6-v2` (local) for privacy.

## Chunking

- **Chunk Size:** 1000 tokens.
- **Overlap:** 200 tokens.
Adjust this in `aurora.yaml` if you find the agent missing context at the boundaries of chunks.

## Semantic Cache

Enable `cache_vectors: true` to cache identical queries in Redis. This saves money on Embedding API calls.

## Related Reading

- [Memory Architecture](../02_architecture/memory_architecture.md)
- [Redis Operations](../09_operations/redis_operations.md)
