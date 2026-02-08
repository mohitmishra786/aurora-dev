# Jira Integration

Enterprise task tracking.

**Last Updated:** February 8, 2026
**Audience:** Project Managers

> **Before Reading This**
>
> You should understand:
> - [Task API](../07_api_reference/task_api.md)
> - [Configuration](../13_configuration/agent_configuration.md)

## Two-Way Sync

- **Jira -> Aurora:** "In Progress" in Jira starts the agent.
- **Aurora -> Jira:** Agent completion updates Jira to "QA".

## Data Mapping

| Jira Field | Aurora Field |
|------------|--------------|
| Summary | Title |
| Description | Description |
| Assignee | Assigned Agent |
| Status | Status |

## Setup

1. Generate an API Token in Atlassian Access.
2. Set `JIRA_URL`, `JIRA_USER`, and `JIRA_TOKEN`.
3. Configure the Project Key (e.g., `PROJ`).

## Related Reading

- [GitHub Integration](./github_integration.md)
- [Custom Integrations](./custom_integrations.md)
