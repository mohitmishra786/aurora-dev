# CLI Commands

The power at your fingertips.

**Last Updated:** February 8, 2026
**Audience:** Developers

## `aurora init`

Initializes a new project in the current directory.
- `--name`: Project name.
- `--template`: `flask`, `django`, `fastapi`, `react`.

## `aurora run`

Starts the agent loop.
- `--task`: Path to task file or raw string.
- `--agent`: Specific agent to run (default: `manager`).
- `--debug`: Enable verbose logging.

## `aurora deploy`

Deploys the project to cloud.
- `--target`: `aws`, `gcp`, `azure`.
- `--env`: `production`, `staging`.

## `aurora doctor`

Diagnoses issues with your environment.
Checks:
- Docker connectivity.
- API Key validity.
- Port availability.

## Related Reading

- [Using CLI](../05_user_guides/using_cli.md)
- [Configuration Options](./configuration_options.md)
