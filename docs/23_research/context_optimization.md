# Context Optimization

Managing the scarce resource of agent attention.

**Last Updated:** February 8, 2026
**Audience:** AI Engineers

> **Before Reading This**
>
> You should understand:
> - [Memory Architecture](../02_architecture/memory_architecture.md)
> - [Prompt Engineering](./prompt_engineering.md)

## The Window Problem

Large Language Models (LLMs) have a finite context window. Claude 3 produces outputs based on ~200,000 tokens of input. While this sounds vast (roughly 500 pages of text), a medium-sized codebase can easily exceed 1 million tokens.

If we blindly stuff every file into the context, we hit two problems:
1. **Cost:** Input tokens are not free. Feeding 200k tokens for every query is bankruptcy speed-run.
2. **Performance:** As context grows, "Reasoning Density" drops. The model gets distracted by irrelevant details (the `utils.py` file mentioned in line 4000) and hallucinating connections that don't exist.

## Strategy: Dynamic Context Window

We treat the context window like a cache. We want the highest "Hit Rate" of relevant information per token.

To achieve this, we use a **Relevance Scoring Algorithm**. When a task arrives ("Fix bug in auth service"), we don't load the entire repo. We load:
1. The `auth_service.py` file (High Relevance).
2. The `user_model.py` file (Medium Relevance, linked via import).
3. The `test_auth.py` file (Medium Relevance).
4. The global `config.py` (Low Relevance, but foundational).

All other files—CSS, frontend components, unrelated utils—are excluded. This reduces the context from 1M tokens to ~5k tokens. The model can now focus.

## Token Compression Techniques

Even with selection, files can be huge. We employ several compression techniques:

### 1. Abstract Syntax Tree (AST) Summarization
Instead of feeding the raw code of a dependency, we feed its **Interface Definition**.

*Raw Code:*
```python
def calculate_tax(amount):
    # ... 50 lines of complex logic ...
    return total
```

*Compressed Context:*
```python
def calculate_tax(amount: float) -> float:
    """Calculates tax based on 2024 rules."""
    ...
```

The agent doesn't need to know *how* tax is calculated to call the function. It just need the signature. This saves 90% of tokens for dependencies.

### 2. Semantic Search Retrieval
We use `pgvector` to find relevant code snippets. We chunk code into functions and index them by semantic meaning. If the task mentions "login," we retrieve the 5 most similar chunks. This is "Just-In-Time" context loading.

### 3. Summarization Layers
For long documents (like this one), we generate a 1-paragraph summary and store it in the vector DB. An agent browsing the docs sees the summary first. If it decides it needs more detail, it requests the full file. This mimics how humans browse a library (Title -> Abstract -> Full Text).

## Metrics

We monitor **Token Utilization Efficiency (TUE)**:
$$ TUE = \frac{\text{Useful Tokens Generated}}{\text{tokens In Context}} $$

A low TUE score means we fed the model garbage. A high TUE means the context was highly relevant to the output.

## Future Research

We are exploring **"Context Caching"** (Anthropic feature) to keep the "Base Context" (framework docs, core utils) hot in the model's memory, reducing cost and latency for sequential requests.

## Related Reading

- [Prompt Engineering](./prompt_engineering.md)
- [Code Generation](./code_generation.md)

## What's Next

- [Code Generation](./code_generation.md)
