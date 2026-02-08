# Workflow Configuration

Customizing execution workflows.

**Last Updated:** February 8, 2026  
**Audience:** Developers

## Configuration

```yaml
workflow:
  parallel_agents: 4
  auto_approve_tests: true
  
  phases:
    planning:
      enabled: true
      timeout_minutes: 30
      require_approval: true
      
    implementation:
      enabled: true
      timeout_minutes: 120
      max_retries: 3
      
    testing:
      enabled: true
      timeout_minutes: 60
      
    review:
      enabled: true
      auto_merge: false
      require_human: true
      
    deployment:
      enabled: false  # Manual trigger
```

## Skip Phases

```bash
aurora build --skip testing
```

## Related Reading

- [Customizing Workflows](../05_user_guides/customizing_workflows.md)
