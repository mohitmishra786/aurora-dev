# Agent Assignment

Putting the right brain on the right problem.

**Last Updated:** February 14, 2026
**Audience:** Project Managers, Architects

> **Before Reading This**
>
> You should understand:
> - [Task Decomposition](./task_decomposition.md)
> - [Agent Specifications](../03_agent_specifications/00_base_agent.md)

## The Hiring Manager

Once a task is defined ("Fix the CSS z-index bug"), who should do it?
- The `Frontend Agent`? (Probably)
- The `UI Designer`? (Maybe)
- The `Backend Agent`? (Definitely not)

Agent Assignment is a classification problem. We map `Task -> Agent Class`.

## The Matching Algorithm

We don't just use keyword matching ("CSS" -> Frontend). We use semantic similarity embedding.

1. **Embed Task:** `Vector(Task Description + Context)`
2. **Embed Profiles:** `Vector(Agent Capability Description)`
3. **Cosine Similarity:** Find highest match.

However, we also apply **Heuristics Overrides**:
- If `file_path` ends in `.py`, boost `Backend` and `DataScience`.
- If `file_path` ends in `.tf`, force `DevOps`.
- If `type` is "security_audit", force `SecurityAuditor`.

## Cost-Based Routing

For generic tasks (e.g., "Write a regex"), multiple agents *could* do it.
- `Claude 3 Opus` (Smartest, Expensive)
- `Claude 3 Haiku` (Fast, Cheap)

We estimate the "Complexity Score" of the task.
- **Score < 3:** Route to Haiku (Cost saving).
- **Score > 7:** Route to Opus (Quality assurance).

This saves ~40% on API bills without sacrificing quality on hard problems.

## Context Window Fit

Before assigning a task, Maestro estimates the token cost of the task (description + acceptance criteria + dependencies) using `estimate_tokens()`. If the estimate exceeds 80% of the target agent's model context limit, the agent scores `0.0` and is excluded:

```python
model_limit = MODEL_CONTEXT_LIMITS.get(agent_model, 128_000)
task_tokens = self._estimate_task_tokens(task)
if task_tokens > model_limit * 0.8:
    return 0.0  # Agent can't fit this task
```

## Scoring Weights

| Factor | Weight | Description |
|--------|--------|-------------|
| Specialization | 0.35 | 1.0 for matching role, 0.3 otherwise |
| Workload | 0.25 | Inverse of active task count |
| Success rate | 0.20 | Historical completion ratio |
| Recency | 0.10 | Fairness based on total assignments |
| Round-robin | 0.10 | Rotation bonus for next expected agent |

## Hand-offs

Sometimes, an agent realizes it's the wrong tool for the job.
> "I am the Backend Agent. I see this error is actually in the Nginx config. I am handing this off to the DevOps Agent."

This "Hot Potato" protocol prevents agents from hallucinating solutions in domains they don't understand.

## Visualization

```mermaid
graph TD
    Task[Incoming Task] --> Classifier{Analyze}
    
    Classifier -->|Complexity: High| Expert[Expert Agent (Opus)]
    Classifier -->|Complexity: Low| Junior[Junior Agent (Haiku)]
    
    Expert -->|Domain: UI| Frontend
    Expert -->|Domain: DB| Database
    
    Backend -->|Stuck| Handoff[Request Handoff]
    Handoff --> Maestro[Maestro Re-assigns]
```

## Related Reading

- [Cost Optimization](./cost_optimization.md)
- [Maestro Agent](../03_agent_specifications/01_maestro_agent.md)

## What's Next

- [Reflexion Loops](./reflexion_loops.md)
