# Cost Troubleshooting

Managing unexpected or high costs.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Diagnosis

```bash
# Check daily costs
aurora costs --daily --breakdown

# Identify expensive tasks
aurora costs --by-task --top 10
```

## Common Causes

| Cause | Solution |
|-------|----------|
| Too many retries | Improve prompts |
| Large context | Reduce context size |
| Opus overuse | Use Sonnet/Haiku |
| Parallel agents | Reduce concurrency |

## Cost Reduction

```yaml
cost_management:
  model_routing:
    expensive_threshold: 0.10
    fallback_model: claude-3-haiku
```

## Budget Alerts

```yaml
cost_management:
  alerts:
    - threshold: 0.75
      action: notify
    - threshold: 0.95
      action: pause
```

## Related Reading

- [Managing Costs](../05_user_guides/managing_costs.md)
