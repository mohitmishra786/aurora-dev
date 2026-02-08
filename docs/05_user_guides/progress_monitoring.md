# Progress Monitoring

Real-time visibility into AURORA-DEV execution.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## CLI Dashboard

```bash
aurora status --watch
```

Live updates:
```
┌─ Project: my-app ─────────────────────────────────┐
│ Phase: IMPLEMENTING (3/4)                         │
│ Progress: ████████████░░░░░░░ 68%                 │
├───────────────────────────────────────────────────┤
│ Active Agents:                                    │
│   🟢 Backend   : Implementing task endpoint       │
│   🟢 Frontend  : Building task list component     │
│   🟡 Database  : Waiting for backend              │
├───────────────────────────────────────────────────┤
│ Completed: 8/12 tasks │ ETA: 10 min │ Cost: $5.20│
└───────────────────────────────────────────────────┘
```

## Web Interface

Access at `http://localhost:8080/dashboard`:
- Real-time task graph
- Agent activity streams
- Cost tracking
- Error logs

## Webhook Notifications

```yaml
notifications:
  webhooks:
    - url: https://api.slack.com/webhooks/xxx
      events: [phase_complete, error, project_done]
```

## Log Streaming

```bash
# All agents
aurora logs --follow

# Specific agent
aurora logs --agent backend --follow
```

## Related Reading

- [Understanding Agent Output](./understanding_agent_output.md)
- [Alerting Rules](../09_operations/alerting_rules.md)
