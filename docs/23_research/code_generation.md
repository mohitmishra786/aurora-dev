# Code Generation: Beyond Autocomplete

Synthesizing robust software from intent.

**Last Updated:** February 8, 2026
**Audience:** AI Researchers, Developers

> **Before Reading This**
>
> You should understand:
> - [Implementation Layer](../02_architecture/implementation_layer.md)
> - [Coding Standards](../06_developer_guides/coding_standards.md)

## The Stochastic Parrot Problem

LLMs are probabilistic. They predict the next token. This is great for writing poems, but terrible for writing C++. A missing semicolon in a poem is "artistic license." A missing semicolon in C++ is a compile error.

In AURORA-DEV, we treat code generation as a **Constrained Search Problem**. We are searching for a sequence of characters that:
1. Satisfies the User Intent.
2. Compiles/Interprets without error.
3. Passes all Unit Tests.
4. Adheres to Style Guidelines.

## The Generation Pipeline

We do not just say "Write code." We use a multi-stage pipeline:

### 1. Planning (Pseudocode)
The agent first generates a high-level plan in natural language or pseudocode.
> "I will create a function `process_data` that iterates through the list, filters by date, and sums the values."

This forces the model to reason about the logic *before* worrying about syntax.

### 2. Implementation (Drafting)
The agent translates the plan into code. We use temperature `0.2` for this step to minimize creativity and maximize adherence to syntax rules.

### 3. Static Analysis (Linting)
Before the code is even saved, we run it through a linter (Ruff/Black for Python). If the linter complains, we feed the error back to the agent:
> "Your code has a syntax error on line 5. Fix it."

This is the first "Inner Loop" of self-correction.

### 4. Dynamic Verification (Testing)
We generate a test case *alongside* the code. We run the code against the test. If it fails, we iterate. This is Test-Driven Development (TDD) at machine speed.

## Managing Dependencies

Hallucinated libraries are a major issue. LLMs love to import `utils.common_helpers` which doesn't exist.

To combat this, we provide the agent with a **"Bill of Materials"**—a list of installed packages and available local modules. If the agent tries to import something not on the list, the environment blocks it and prompts for a correction.

## The Role of Templates

We don't start from a blank canvas. We use **Scaffolding**. When asking for a React component, we provide the file structure:
```tsx
import React from 'react';
// interactions...

export const ComponentName = () => {
    // logic...
    return (
        // JSX...
    );
};
```
This primes the model to follow our specific architectural patterns (e.g., Functional Components vs Class Components).

## Future Research

We are investigating **"Grammar-Constrained Decoding"**. This allows us to force the LLM to output valid AST nodes at the token level, making syntax errors mathematically impossible.

## Related Reading

- [Coding Standards](../06_developer_guides/coding_standards.md)
- [Reflexion Paper](./reflexion_paper.md)

## What's Next

- [Future Directions](./future_directions.md)
