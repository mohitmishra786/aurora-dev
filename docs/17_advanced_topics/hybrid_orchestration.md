# Hybrid Orchestration

Humans and machines together.

**Last Updated:** February 8, 2026
**Audience:** PMs

> **Before Reading This**
>
> You should understand:
> - [Agent Swarms](./agent_swarms.md)
> - [Quality Gates](../04_core_concepts/quality_gates.md)

## The 80/20 Rule

AI does 80% of the work (boilerplate, tests).
Humans do 20% of the work (high-level design, final review).

## Handoff Protocol

When an agent hits a wall (e.g., Circular Dependency), it raises a `HumanInterventionRequired` exception.
The Dashboard alerts the user: "Agent is stuck. Please advise."
The user types a hint: "Try removing the import of X in file Y."
The agent resumes.

## Trust Score

We track a "Trust Score" for each agent.
If the score drops below threshold, the agent enters "Probation" and requires approval for every step.

## Related Reading

- [Quality Gates](../04_core_concepts/quality_gates.md)
- [Interpreting Results](../05_user_guides/interpreting_results.md)
