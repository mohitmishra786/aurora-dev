# GitHub Integration

Connecting code to task.

**Last Updated:** February 8, 2026
**Audience:** Integrators

> **Before Reading This**
>
> You should understand:
> - [Task Decomposition](../04_core_concepts/task_decomposition.md)
> - [Configuration](../13_configuration/agent_configuration.md)

## Features

1. **PR Reviews:** The `Code Reviewer Agent` automatically comments on open PRs.
2. **Issue Sync:** Creating a GitHub Issue creates an Aurora Task.
3. **Commit Tracing:** Mentioning `Task-123` in a commit links the code to the task in the dashboard.

## Setup

1. Create a GitHub App.
2. Grant Permissions: `Pull Requests (Write)`, `Issues (Write)`, `Contents (Read)`.
3. Set `GITHUB_APP_ID` and `GITHUB_PRIVATE_KEY` in `.env`.

## Webhook Handling

We listen for `pull_request.opened` events.
The webhook endpoint is `https://api.aurora.dev/webhooks/github`.
Ensure you set a `WEBHOOK_SECRET` to verify signatures.

## Related Reading

- [GitLab Integration](./gitlab_integration.md)
- [Jira Integration](./jira_integration.md)
