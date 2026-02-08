# Model Selection

Choosing the right brain for the job.

**Last Updated:** February 8, 2026
**Audience:** Architects

> **Before Reading This**
>
> You should understand:
> - [Agent Configuration](./agent_configuration.md)
> - [Managing Costs](../05_user_guides/managing_costs.md)

## Recommended Models

| Task Type | Model | Reason |
|-----------|-------|--------|
| **Coding (Complex)** | `claude-3-opus` | Best reasoning capability. Less bugs. |
| **Coding (Simple)** | `claude-3-sonnet` | Fast and cheap. Good for refactoring. |
| **Chat / Q&A** | `gpt-4o` | Native creativity. |
| **Summarization** | `claude-3-haiku` | Extremely fast and cheap. |

## Fallback Strategy

If `claude-3-opus` is down or rate-limited, the system automatically falls back to `gpt-4-turbo`. This ensures high availability.

## Local Models

We support Ollama for local inference.
Set `model: ollama/llama3`.
Note: Local models are significantly weaker than cloud models. Expect failures on complex tasks.

## Related Reading

- [Managing Costs](../05_user_guides/managing_costs.md)
- [Agent Specifications](../03_agent_specifications/00_base_agent.md)
