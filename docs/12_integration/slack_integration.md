# Slack Integration

ChatOps.

**Last Updated:** February 8, 2026
**Audience:** All Users

> **Before Reading This**
>
> You should understand:
> - [Notification System](../09_operations/alerting_rules.md)
> - [Configuration](../13_configuration/agent_configuration.md)

## The Bot

Adding `@Aurora` to a channel allows you to chat with the system.
`@Aurora creates a task for me.`

## Setup

1. Create a Slack App.
2. Enable Socket Mode (for local dev) or Request URL (for prod).
3. Scopes: `app_mentions:read`, `chat:write`.

## Interactivity

The bot posts Interactive Buttons.
"Agent finished task X. [Approve] [Reject]"
Clicking Approve triggers the API callback.

## Related Reading

- [Teams Integration](./teams_integration.md)
- [Twilio Integration](./twilio_integration.md)
