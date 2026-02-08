# Customizing Workflows

Tailoring AURORA-DEV's execution patterns to your needs.

**Last Updated:** February 8, 2026  
**Audience:** Advanced Users

## Workflow Configuration

Edit `aurora.yaml`:

```yaml
workflow:
  parallel_agents: 4          # Max concurrent agents
  auto_approve_tests: true    # Skip review if tests pass
  require_security_scan: true # Block on security issues
  
  phases:
    planning:
      timeout_minutes: 30
      require_approval: true
      
    implementation:
      timeout_minutes: 120
      max_retries: 3
      
    review:
      auto_merge: false
      require_human: true
```

## Custom Quality Gates

```yaml
quality_gates:
  coverage:
    threshold: 90
    blocking: true
    
  security:
    scan_dependencies: true
    block_on: [critical]
    
  performance:
    p95_latency_ms: 200
    blocking: false
```

## Skipping Phases

```bash
# Skip tests (not recommended)
aurora build --skip-tests

# Skip documentation
aurora build --skip-docs

# Planning only
aurora plan
```

## Related Reading

- [Quality Gates](../04_core_concepts/quality_gates.md)
- [Workflow Configuration](../13_configuration/workflow_configuration.md)
