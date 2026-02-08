# Multi-Project Management

Managing multiple AURORA-DEV projects.

**Last Updated:** February 8, 2026  
**Audience:** Team Leads

## Project Registry

```bash
aurora projects list
```

```
┌──────────────┬───────────┬───────────┬──────────┐
│ Project      │ Status    │ Cost      │ Updated  │
├──────────────┼───────────┼───────────┼──────────┤
│ my-app       │ COMPLETE  │ $45.20    │ 2 hrs    │
│ internal-api │ RUNNING   │ $12.30    │ now      │
│ docs-site    │ PAUSED    │ $3.50     │ 1 day    │
└──────────────┴───────────┴───────────┴──────────┘
```

## Resource Allocation

```yaml
resource_management:
  max_concurrent_projects: 3
  project_priorities:
    - project: internal-api
      priority: high
      agent_limit: 5
    - project: docs-site
      priority: low
      agent_limit: 2
```

## Shared Patterns

Projects can share learned patterns:

```yaml
pattern_sharing:
  enabled: true
  scope: organization  # or 'team', 'global'
```

## Bulk Operations

```bash
# Pause all non-critical projects
aurora projects pause --priority low

# Resume specific project
aurora projects resume internal-api
```

## Related Reading

- [Pattern Library](../04_core_concepts/pattern_library.md)
- [Memory Architecture](../02_architecture/memory_architecture.md)
