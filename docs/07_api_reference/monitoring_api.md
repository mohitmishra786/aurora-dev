# Monitoring API

Health and stats.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Monitoring Agent](../03_agent_specifications/16_monitoring_agent.md)
> - [REST API](./rest_api.md)

## Health Check

`GET /health`

Returns 200 OK if system is alive.
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600
}
```

## Metrics

`GET /metrics`

Returns Prometheus-formatted metrics.
```text
# HELP aurora_requests_total Total requests
# TYPE aurora_requests_total counter
aurora_requests_total{method="post"} 102
aurora_llm_tokens_total{model="claude-3"} 50000
```

## Logs

`GET /logs`

Retrieve recent system logs. Supports filtering.
Query Params: `?level=ERROR&limit=100`

## Cost Analysis

`GET /stats/costs`

Returns daily spend.
```json
{
  "today": 5.43,
  "month_to_date": 120.00,
  "by_agent": {
    "backend": 80.00,
    "frontend": 40.00
  }
}
```

## Related Reading

- [Monitoring Setup](../09_operations/monitoring_setup.md)
- [Managing Costs](../05_user_guides/managing_costs.md)
