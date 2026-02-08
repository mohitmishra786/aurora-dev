# Architecture Decisions

Why we built it this way.

**Last Updated:** February 8, 2026
**Audience:** Architects

> **Before Reading This**
>
> You should understand:
> - [System Architecture](../02_architecture/system_overview.md)
> - [Comparison](../18_business/comparison.md)

## ADR 001: Python over Go

**Context:** We needed a language for the core logic.
**Decision:** Python.
**Reason:** The AI ecosystem (PyTorch, LangChain) is native to Python. Bridging to Go for every LLM call would be high friction.

## ADR 002: Postgres over Mongo

**Context:** Storing structured task data.
**Decision:** Postgres (with JSONB).
**Reason:** Relational integrity is crucial for multi-agent coordination. JSONB gives us the flexibility of NoSQL for task payloads.

## ADR 003: Qdrant over Pinecone

**Context:** Vector database.
**Decision:** Qdrant.
**Reason:** Open Source, Rust-based (fast), and self-hostable. Pinecone is cloud-only SaaS.

## Related Reading

- [System Overview](../02_architecture/system_overview.md)
- [Bibliography](./bibliography.md)
