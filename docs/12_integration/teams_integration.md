# Microsoft Teams Integration

For the corporate world.

**Last Updated:** February 8, 2026
**Audience:** Enterprise Users

> **Before Reading This**
>
> You should understand:
> - [Slack Integration](./slack_integration.md)
> - [Configuration](../13_configuration/agent_configuration.md)

## Adaptive Cards

We use Adaptive Cards to render rich UI in Teams chat.
Similar functionality to Slack: mentions, task updates, approval buttons.

## Setup

1. Create a Bot in Azure Bot Service.
2. Set `TEAMS_APP_ID` and `TEAMS_APP_PASSWORD`.
3. Enable the "MS Teams" channel in Azure.

## Related Reading

- [Slack Integration](./slack_integration.md)
- [Azure Deployment](../08_deployment/cloud_azure.md)
