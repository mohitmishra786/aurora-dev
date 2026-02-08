# GitLab Integration

For the self-hosted crowd.

**Last Updated:** February 8, 2026
**Audience:** Integrators

> **Before Reading This**
>
> You should understand:
> - [GitHub Integration](./github_integration.md)
> - [Configuration](../13_configuration/agent_configuration.md)

## Features

Identical to GitHub: PR Reviews, Issue Sync, Commit Tracing.

## Setup

1. Create a Group Access Token with `api` scope.
2. Set `GITLAB_URL` (defaults to `gitlab.com`).
3. Set `GITLAB_TOKEN` in `.env`.

## CI/CD Pipeline

Add this to `.gitlab-ci.yml` to trigger a task on push:

```yaml
aurora-check:
  image: aurora/cli
  script:
    - aurora check --ci
```

## Related Reading

- [GitHub Integration](./github_integration.md)
- [Custom Integrations](./custom_integrations.md)
