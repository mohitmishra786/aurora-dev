# aurora.yaml Reference

Complete configuration file reference.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Full Example

```yaml
# aurora.yaml
project:
  name: my-app
  version: 1.0.0
  type: fullstack

agents:
  parallel: 4
  default_model: claude-3-sonnet-20240229
  
  maestro:
    model: claude-3-sonnet-20240229
  architect:
    model: claude-3-opus-20240229
  backend:
    model: claude-3-sonnet-20240229
    temperature: 0.3

workflow:
  phases:
    planning:
      timeout_minutes: 30
    implementation:
      timeout_minutes: 120

quality_gates:
  coverage:
    threshold: 80
    blocking: true
  security:
    block_on: [critical, high]

cost_management:
  daily_budget: 100.00
  monthly_budget: 2000.00

integrations:
  github:
    enabled: true
```

## Related Reading

- [Environment Variables](./environment_variables.md)
