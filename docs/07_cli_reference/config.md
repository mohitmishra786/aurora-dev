# CLI Reference: Config

Manage AURORA-DEV configuration.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Synopsis

```bash
aurora config [COMMAND] [OPTIONS]
```

## Commands

| Command | Description |
|---------|-------------|
| `show` | Display current config |
| `set` | Set a config value |
| `get` | Get a config value |
| `reset` | Reset to defaults |

## Examples

```bash
aurora config show
aurora config set agents.parallel 4
aurora config get cost_management.daily_budget
aurora config reset --confirm
```

## See Also

- [Environment Variables](../13_configuration/environment_variables.md)
