# Advanced Reflexion

Thinking about thinking.

**Last Updated:** February 8, 2026
**Audience:** Researchers

> **Before Reading This**
>
> You should understand:
> - [Reflexion Loops](../04_core_concepts/reflexion_loops.md)
> - [Reflexion Paper](../23_research/reflexion_paper.md)

## Binary Feedback

Standard reflexion uses "Pass/Fail".
Advanced reflexion uses scalar feedback. "Your code is 80% correct but inefficient."

## Semantic Memory

The agent stores its past mistakes in Qdrant.
Before starting a task, it queries: "Have I failed at this before?"
It retrieves: "Yes, you forgot to handle TypeError last time."
It adds a note to self: "Remember to handle TypeError."

## Language Refinement

The agent rewrites its own System Prompt based on success/failure rates.
This is "Meta-Learning."

## Related Reading

- [Reflexion Loops](../04_core_concepts/reflexion_loops.md)
- [Context Optimization](../23_research/context_optimization.md)
