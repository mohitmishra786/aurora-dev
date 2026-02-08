# Token Optimization

Saving pennies.

**Last Updated:** February 8, 2026
**Audience:** Architects

> **Before Reading This**
>
> You should understand:
> - [Managing Costs](../05_user_guides/managing_costs.md)
> - [Model Selection](../13_configuration/model_selection.md)

## Compression

The `ContextManager` automatically compresses prompts.
1. **Whitespace removal:** Strips extra newlines.
2. **Tree shaking:** Removes unused functions from the code context.
3. **Summarization:** Replaces old chat history with a bulleted summary.

## Tool Definitions

Define tools concisely.
Docstrings count towards tokens.
*Bad:* "This function adds two numbers and returns the sum of them."
*Good:* "Add entries."

## Caching

We cache LLM responses. If the exact same prompt is sent (temperature=0), we return the cached result.

## Related Reading

- [Managing Costs](../05_user_guides/managing_costs.md)
- [Context Management](../04_core_concepts/context_management.md)
