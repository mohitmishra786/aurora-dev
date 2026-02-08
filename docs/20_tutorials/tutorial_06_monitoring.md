# Tutorial 06: Monitoring

Keeping watch.

**Last Updated:** February 8, 2026
**Difficulty:** Advanced
**Time:** 20 mins

## Goal

Add Prometheus metrics and Grafana dashboard.

## Step 1: Task Definition

```markdown
# Objective
Add `prometheus-fastapi-instrumentator` to `main.py`.
Expose metrics at `/metrics`.
Update `docker-compose.yaml` to include Prometheus and Grafana services.
```

## Step 2: Run Agent

```bash
aurora run --task task.md --agent monitoring
```

## Step 3: View Dashboard

Go to `http://localhost:3000` (Grafana).
Add Prometheus data source (`http://prometheus:9090`).
Import dashboard ID `1`.

## Next Step

[Tutorial 07: Custom Agent](./tutorial_07_custom_agent.md)
