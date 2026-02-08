# Appendix C: Default Configuration

The `aurora.yaml` you get out of the box.

**Last Updated:** February 8, 2026
**Audience:** All Users

> **Before Reading This**
>
> You should understand:
> - [Configuration Guide](../13_configuration/aurora_yaml_reference.md)

## Default Values

Unless you override them, these are the settings AURORA-DEV uses.

```yaml
version: "2.1"

# Project Defaults
project:
  type: fullstack
  frameworks:
    backend: fastapi
    frontend: react
    database: postgresql

# Agent Defaults
agents:
  default:
    model: claude-3-sonnet-20240229
    temperature: 0.5
    max_tokens: 4096
    timeout: 120s
    retry_count: 3
    
  architect:
    model: claude-3-opus-20240229
    temperature: 0.7

# Memory Defaults
memory:
  short_term:
    ttl: 3600
  long_term:
    min_score: 0.8

# Pipeline Defaults
pipeline:
  parallel_tasks: 4
  auto_fix: true
  test_on_save: true

# Logging
logging:
  level: INFO
  file_path: .aurora/logs/execution.log
```

## Overriding

You can override any value in your project's `aurora.yaml` or via environment variables:
`AURORA_AGENTS_DEFAULT_MODEL=gpt-4`

## Related Reading

- [Configuration Guide](../13_configuration/aurora_yaml_reference.md)
