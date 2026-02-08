# Logging Configuration

Control the noise.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Logging Setup](../09_operations/logging_setup.md)
> - [Environment Variables](./environment_variables.md)

## Log Levels

Can be set globally or per module.
```yaml
logging:
  level: INFO
  loggers:
    aurora.db: WARNING
    aurora.agent: DEBUG
```

## Formatters

- **JSON:** Production default.
- **Console:** Development default. Colored output.

## Trace Headers

We look for `X-Trace-Id` header. If missing, we generate one.
This ID is included in every log message to correlate requests across microservices.

## Sensitive Data

We use a `PIIFilter` to redact:
- Credit Card Numbers.
- API Keys.
- Social Security Numbers.

## Related Reading

- [Logging Setup](../09_operations/logging_setup.md)
- [Debugging Agents](../06_developer_guides/debugging_agents.md)
