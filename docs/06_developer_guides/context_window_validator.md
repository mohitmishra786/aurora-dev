# Context Window Validator

Token estimation and smart truncation for managing LLM context limits.

**Last Updated:** February 14, 2026  
**Audience:** Developers, AI Engineers

> **Before Reading This**
>
> You should understand:
> - [Context Management](../04_core_concepts/context_management.md) - Concepts
> - [Agent Assignment](../04_core_concepts/agent_assignment.md) - Scoring algorithm

## Overview

The `ContextWindowValidator` (`aurora_dev/core/context_window.py`) provides utilities for estimating token counts, validating that prompts fit within model context limits, and performing intelligent truncation when they don't.

## Key Functions

### Token Estimation

```python
from aurora_dev.core.context_window import estimate_tokens

# Quick estimate (~4 chars per token)
token_count = estimate_tokens("Your text here")

# Estimate for a list of messages
from aurora_dev.core.context_window import estimate_messages_tokens
total = estimate_messages_tokens([
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_message},
])
```

### Model Context Limits

```python
from aurora_dev.core.context_window import MODEL_CONTEXT_LIMITS

MODEL_CONTEXT_LIMITS = {
    "claude-3-opus-20240229": 200_000,
    "claude-3-5-sonnet-20241022": 200_000,
    "claude-3-sonnet-20240229": 200_000,
    "claude-3-haiku-20240307": 200_000,
    "gpt-4o": 128_000,
    "gpt-4-turbo": 128_000,
    # ...
}
```

### Smart Truncation

When content exceeds the context limit, the validator truncates from the **middle** of the text, preserving the start (instructions) and end (target code) — this combats the "lost in the middle" phenomenon:

```python
from aurora_dev.core.context_window import ContextWindowValidator

validator = ContextWindowValidator(model="claude-3-5-sonnet-20241022")

# Check if content fits
fits = validator.fits(content, reserved_output_tokens=4096)

# Truncate if needed (preserves start + end)
truncated = validator.truncate(
    content,
    max_tokens=150_000,
    strategy="middle"  # or "end"
)
```

## Integration with Maestro

The `MaestroAgent._score_agent()` method uses context window validation to reject agents that can't fit a task:

```python
# In maestro.py
task_tokens = self._estimate_task_tokens(task)
model_limit = MODEL_CONTEXT_LIMITS.get(agent_model, 128_000)
if task_tokens > model_limit * 0.8:
    return 0.0  # Agent excluded from assignment
```

The 80% threshold reserves space for system prompts, memory context, and output generation.

## Usage Report

```python
# Get a formatted report of token usage vs capacity
report = validator.usage_report(
    system_prompt=system_prompt,
    messages=messages,
    memory_context=context,
)
print(report)
# Output: "Token usage: 45,230 / 200,000 (22.6%)"
```

## Related Reading

- [Context Management](../04_core_concepts/context_management.md) - Retrieval strategies
- [Agent Assignment](../04_core_concepts/agent_assignment.md) - Scoring with context fit
- [Memory Architecture](../02_architecture/memory_architecture.md) - Data flow into context

## What's Next

- [Cross-Encoder Reranker](./cross_encoder_reranker.md) - Search result quality
