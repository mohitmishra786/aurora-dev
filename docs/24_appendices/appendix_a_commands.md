# Appendix A: Command Reference

The fast lookup for every `aurora` CLI command.

**Last Updated:** February 8, 2026
**Audience:** All Users

> **Before Reading This**
>
> You should understand:
> - [CLI Tool](../07_cli_reference/overview.md)

## Core Commands

| Command | Description | Flags |
|---------|-------------|-------|
| `aurora init` | Create new project | `-t, --template <name>` |
| `aurora run` | Start agents | `-p, --parallel <n>` |
| `aurora stop` | Stop execution | `--force` |
| `aurora status` | Show current task | `--watch` |

## Task Management

| Command | Description | Example |
|---------|-------------|---------|
| `aurora task add` | Queue new task | `aurora task add "Fix login"` |
| `aurora task list` | View queue | `aurora task list --status pending` |
| `aurora task retry` | Re-run failed task | `aurora task retry <uuid>` |

## Agent Management

| Command | Description | Example |
|---------|-------------|---------|
| `aurora agent list` | Show registered agents | `aurora agent list` |
| `aurora agent logs` | View logs | `aurora agent logs backend -f` |
| `aurora agent reset` | Clear agent state | `aurora agent reset frontend` |

## Memory & config

| Command | Description | Example |
|---------|-------------|---------|
| `aurora memory search` | Query vector DB | `aurora memory search "auth pattern"` |
| `aurora config show` | Dump active config | `aurora config show --json` |
| `aurora config validate` | Check schema | `aurora config validate` |

## Development

| Command | Description | Example |
|---------|-------------|---------|
| `aurora dev` | Start dev server | `aurora dev --watch` |
| `aurora test` | Run test suite | `aurora test --unit` |
| `aurora lint` | Fix code style | `aurora lint --fix` |

## Related Reading

- [CLI Reference](../07_cli_reference/index.md)
