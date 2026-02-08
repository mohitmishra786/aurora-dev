# Tutorial 10: Advanced

The final boss.

**Last Updated:** February 8, 2026
**Difficulty:** Expert
**Time:** 45 mins

## Goal

Create a multi-agent workflow that:
1. Scrapes a website (Integration Agent).
2. Summarizes it (Backend Agent).
3. Posts summary to Slack (Integration Agent).
4. Saves it to DB (Database Agent).

## Step 1: Workflow Definition

Create `workflow.yaml`:
```yaml
steps:
  - name: scrape
    agent: integration
    instruction: "Scrape content from url"
  - name: summarize
    agent: backend
    instruction: "Summarize the content"
    inputs: [scrape.output]
  - name: notify
    agent: integration
    instruction: "Post summary to Slack"
    inputs: [summarize.output]
```

## Step 2: Run

```bash
aurora run-workflow workflow.yaml
```

## Congratulations!

You are now an Aurora Expert.
