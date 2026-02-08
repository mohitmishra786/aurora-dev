# Logging Setup

Structured logs for structured minds.

**Last Updated:** February 8, 2026
**Audience:** Developers, DevOps

> **Before Reading This**
>
> You should understand:
> - [Logging Configuration](../13_configuration/logging_configuration.md)
> - [Monitoring Setup](./monitoring_setup.md)

## Format

We output JSON logs to stdout.
```json
{
  "timestamp": "2026-02-08T12:00:00Z",
  "level": "INFO",
  "logger": "aurora.agents.backend",
  "message": "Generating code for Task 123",
  "task_id": "123",
  "trace_id": "abc-def"
}
```

## Aggregation

Do not read logs with `docker logs`. Use a centralized system.
- **ELK Stack:** Filebeat -> Logstash -> Elasticsearch -> Kibana.
- **Loki:** Promtail -> Loki -> Grafana.
- **Cloud:** CloudWatch / Stackdriver.

## Log Levels

- **DEBUG:** Raw prompts/responses. Huge volume.
- **INFO:** High-level state changes ("Task Started").
- **WARNING:** Retryable errors ("API Timeout").
- **ERROR:** Crash or bug ("NullPointerException").

## Retention Policy

- **DEBUG:** 3 days.
- **INFO:** 30 days.
- **ERROR:** 1 year (for Auditing).

## Related Reading

- [Logging Configuration](../13_configuration/logging_configuration.md)
- [Debugging Failures](../05_user_guides/debugging_failures.md)
