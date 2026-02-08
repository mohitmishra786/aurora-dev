# Model Comparison

Battle of the brains.

**Last Updated:** February 8, 2026
**Audience:** Architects

> **Before Reading This**
>
> You should understand:
> - [Model Selection](../13_configuration/model_selection.md)
> - [Benchmarks](../16_performance/benchmarks.md)

## GPT-4o (OpenAI)

- **Pros:** Best overall reasoning. Fast. Multi-modal (Vision).
- **Cons:** Expensive.
- **Best Use:** Complex coding, architecting.

## Claude 3 Opus (Anthropic)

- **Pros:** Massive context window (200k). Very descriptive. Low hallucination.
- **Cons:** Slower than GPT-4o.
- **Best Use:** Reading entire codebases, writing documentation.

## Llama 3 (Meta)

- **Pros:** Open Weights. Free to run (if you have GPUs). Private.
- **Cons:** Weaker reasoning than GPT/Claude.
- **Best Use:** Local dev, private data processing.

## Related Reading

- [Model Selection](../13_configuration/model_selection.md)
- [Configuration Options](./configuration_options.md)
