# Environment Variables

The twelve-factor configuration.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Docker Deployment](../08_deployment/docker_deployment.md)
> - [Secrets Management](../10_security/secrets_management.md)

## Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `AURORA_ENV` | `development` | `production`, `staging`, `development`. |
| `LOG_LEVEL` | `INFO` | Logging verbosity. |
| `SECRET_KEY` | *(Required)* | For JWT signing. |

## Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | Postgres Host. |
| `DB_PORT` | `5432` | Postgres Port. |
| `DB_USER` | `aurora` | Postgres User. |
| `DB_PASS` | *(Required)* | Postgres Password. |

## AI Models

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | Required if using GPT models. |
| `ANTHROPIC_API_KEY` | - | Required if using Claude models. |

## Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_WEB_SEARCH` | `false` | Enable/Disable web browsing capability. |
| `ENABLE_EXPERIMENTAL` | `false` | Enable beta features. |

## Related Reading

- [Agent Configuration](./agent_configuration.md)
- [Secrets Management](../10_security/secrets_management.md)
