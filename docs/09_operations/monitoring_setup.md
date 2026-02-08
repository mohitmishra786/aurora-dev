# Monitoring Setup

Eyes on the prize.

**Last Updated:** February 8, 2026
**Audience:** SREs

> **Before Reading This**
>
> You should understand:
> - [Monitoring Agent](../03_agent_specifications/16_monitoring_agent.md)
> - [Alerting Rules](./alerting_rules.md)

## Prometheus Configuration

Add this job to `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'aurora'
    static_configs:
      - targets: ['aurora-server:8000']
    metrics_path: '/metrics'
```

## Grafana Dashboards

Import `dashboards/main.json` into Grafana.
Panels included:
- **RPS (Requests Per Second)**
- **Error Rate (5xx)**
- **LLM Token Usage**
- **Agent Busy Threads**

## Key Metrics to Watch

- `aurora_task_duration_seconds`: Is usage getting slower?
- `aurora_agent_failures_total`: Are agents crashing?
- `aurora_db_connection_count`: Are we leaking connections?

## Distributed Tracing

We support OpenTelemetry. Point `OTEL_EXPORTER_OTLP_ENDPOINT` to your Jaeger/Tempo instance to see full flame graphs of agent reasoning.

## Related Reading

- [Alerting Rules](./alerting_rules.md)
- [Logging Setup](./logging_setup.md)
