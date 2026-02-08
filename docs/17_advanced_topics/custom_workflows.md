# Custom Workflows

Beyond simple tasks.

**Last Updated:** February 8, 2026
**Audience:** Architects

> **Before Reading This**
>
> You should understand:
> - [Task Decomposition](../04_core_concepts/task_decomposition.md)
> - [Custom Agent Development](./custom_agent_development.md)

## Map-Reduce

1. **Map:** Split a large document into 100 chunks.
2. **Process:** Run 100 agents in parallel to summarize each chunk.
3. **Reduce:** One agent combines the summaries into a final report.

## Human-in-the-Loop

1. Agent generates a Plan.
2. Workflow pauses.
3. Sends Slack notification with "Approve / Reject" button.
4. Human clicks Approve -> Agent continues.

## Defining Workflows

We use a Python DSL.
```python
workflow = Workflow()
workflow.add_step(FetchData())
workflow.add_step(AnalyzeData(), parents=[FetchData])
workflow.run()
```

## Related Reading

- [Agent Swarms](./agent_swarms.md)
- [Parallel Execution](../16_performance/parallel_execution.md)
