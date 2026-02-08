# Tutorial 08: Integration

Connecting to Slack.

**Last Updated:** February 8, 2026
**Difficulty:** Advanced
**Time:** 20 mins

## Goal

Send a notification to Slack when a task is created.

## Step 1: Setup

Get a Slack Webhook URL.
Add to `.env`: `SLACK_WEBHOOK_URL=https://hooks.slack.com/...`

## Step 2: Task Definition

```markdown
# Objective
Modify `main.py`.
In the `create_task` endpoint, send a POST request to `os.getenv("SLACK_WEBHOOK_URL")` with the task title.
```

## Step 3: Run Agent

```bash
aurora run --task task.md --agent integration
```

## Next Step

[Tutorial 09: Optimization](./tutorial_09_optimization.md)
