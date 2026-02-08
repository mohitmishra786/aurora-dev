# Agent Assignment

Putting the right brain on the right problem.

**Last Updated:** February 8, 2026
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
