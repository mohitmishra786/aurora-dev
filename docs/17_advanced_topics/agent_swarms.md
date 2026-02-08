# Agent Swarms

There is strength in numbers.

**Last Updated:** February 8, 2026
**Audience:** Architects

> **Before Reading This**
>
> You should understand:
> - [Agent Assignment](../04_core_concepts/agent_assignment.md)
> - [Custom Workflows](./custom_workflows.md)

## Hierarchy vs Mesh

- **Hierarchy:** CEO -> Manager -> Worker. Reliable, controlled.
- **Mesh:** Every agent talks to every other. Creative, chaotic.

## The Moderator

In a swarm, we introduce a `Moderator` agent.
Its job is to resolve conflicts.
"Backend says X, Frontend says Y. Moderator decides Z."

## Chat Room Pattern

We create a virtual chat room where agents message each other.
The `Maestro` observes the chat and declares the task done when consensus is reached.

## Related Reading

- [Hybrid Orchestration](./hybrid_orchestration.md)
- [Multi-Agent Systems](../23_research/multi_agent_systems.md)
