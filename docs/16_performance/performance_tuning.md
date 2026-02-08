# Performance Tuning

Optimizing AURORA-DEV execution speed.

**Last Updated:** February 8, 2026  
**Audience:** DevOps Engineers

## Optimization Areas

| Area | Impact | Effort |
|------|--------|--------|
| Parallel agents | High | Low |
| Model selection | Medium | Low |
| Context pruning | Medium | Medium |
| Caching | Medium | Low |

## Increase Parallelism

```yaml
agents:
  parallel: 8  # Default is 4
```

## Enable Caching

```yaml
agents:
  caching:
    enabled: true
    ttl: 3600
```

## Reduce Context Size

```yaml
agents:
  context:
    max_tokens: 50000
    aggressive_pruning: true
```

## Profile Bottlenecks

```bash
aurora run --profile
```

View results in `reports/profile.html`.

## Related Reading

- [Token Optimization](./token_optimization.md)
- [Database Optimization](./database_optimization.md)
