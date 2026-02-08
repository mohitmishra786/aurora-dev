# Memory API

Accessing the knowledge base.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Memory Architecture](../02_architecture/memory_architecture.md)
> - [REST API](./rest_api.md)

## Search

`POST /memory/search`

Perform a semantic search.

Request:
```json
{
  "query": "How do I create a user?",
  "limit": 5,
  "threshold": 0.7,
  "filters": {
    "type": "code"
  }
}
```

## Add Document

`POST /memory/add`

Ingest text into the vector store.

Request:
```json
{
  "content": "def foo(): pass",
  "metadata": {
    "filename": "foo.py",
    "language": "python"
  }
}
```

## Delete Document

`DELETE /memory/{id}`

Remove a specific chunk from the index.

## Reindex

`POST /memory/reindex`

Triggers a background job to re-calculate embeddings for all documents. Useful if you change the Embedding Model.

## Related Reading

- [Memory Configuration](../13_configuration/memory_configuration.md)
- [Extending Memory](../06_developer_guides/extending_memory.md)
