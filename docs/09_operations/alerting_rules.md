# Alerting Rules

Wake up only when necessary.

**Last Updated:** February 8, 2026
**Audience:** SREs

> **Before Reading This**
>
> You should understand:
> - [Monitoring Setup](./monitoring_setup.md)
> - [Incident Response](./incident_response.md)

## The Philosophy

Alert on **Symptoms**, not **Causes**.
- **Good:** "High Error Rate on Checkout" (Symptom).
- **Bad:** "CPU > 80%" (Cause). The CPU *should* be used.

## Prometheus Rules

Defined in `deploy/prometheus/rules.yaml`.

```yaml
groups:
- name: aurora
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "API is failing"
```

## Severity Levels

1. **Critical (Page):** System is unusable. Wakes up on-call.
2. **Warning (Ticket):** Degraded performance. Add to Jira backlog.
3. **Info (Log):** Just for record.

## Routing

Use Elastic Alertmanager.
- **Critical** -> PagerDuty
- **Warning** -> Slack `#ops-alerts`

## Related Reading

- [Incident Response](./incident_response.md)
- [Monitoring Setup](./monitoring_setup.md)
