# Managing Costs

Controlling API usage and optimizing spending.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Cost Visibility

```bash
aurora costs --daily
```

```
┌──────────────────────────────────────────┐
│ Daily Cost Report - Feb 8, 2024          │
├──────────────────────────────────────────┤
│ Opus:   $12.50 (25% of daily)            │
│ Sonnet: $31.20 (62% of daily)            │
│ Haiku:  $6.30  (13% of daily)            │
├──────────────────────────────────────────┤
│ Total:  $50.00 / $100.00 budget          │
└──────────────────────────────────────────┘
```

## Budget Configuration

```yaml
cost_management:
  daily_budget: 100.00
  monthly_budget: 2000.00
  
  alerts:
    - threshold: 0.5
      channel: slack
    - threshold: 0.8
      channel: email
    - threshold: 0.95
      channel: pager
  
  auto_pause_at: 0.95
```

## Cost Reduction Strategies

| Strategy | Savings | Trade-off |
|----------|---------|-----------|
| Use Haiku for tests/docs | 30-40% | Slightly lower quality |
| Enable caching | 10-20% | Stale results possible |
| Reduce context size | 15-25% | Less informed decisions |
| Batch small projects | 5-10% | Delayed starts |

## Related Reading

- [Cost Optimization](../04_core_concepts/cost_optimization.md)
- [Model Selection](../13_configuration/model_selection.md)
