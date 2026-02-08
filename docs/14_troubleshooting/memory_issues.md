# Memory Issues

Amnesia and confusion.

**Last Updated:** February 8, 2026
**Audience:** Backend Developers

> **Before Reading This**
>
> You should understand:
> - [Memory Architecture](../02_architecture/memory_architecture.md)
> - [Memory Configuration](../13_configuration/memory_configuration.md)

## Missing Context

"The agent doesn't know about `User.py`."
*Diagnosis:* Check if `User.py` is in the vector store.
`aurora memory search "User class"`
*Fix:* Run `aurora memory reindex`.

## Slow Retrieval

Search takes > 2 seconds.
*Diagnosis:* Vector store index is cold.
*Fix:* Ensure Qdrant is running on SSD. Enable HNSW index.

## Duplicate Memories

The agent finds 5 copies of the same function.
*Diagnosis:* The file was indexed 5 times without deleting old chunks.
*Fix:* The `Watcher` should handle updates. Check if `file_watcher` service is running.

## Related Reading

- [Memory Configuration](../13_configuration/memory_configuration.md)
- [Redis Operations](../09_operations/redis_operations.md)
