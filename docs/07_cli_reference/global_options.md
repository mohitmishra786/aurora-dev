# CLI Reference: Global Options

Options available to all AURORA-DEV commands.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--help` | `-h` | Show help |
| `--version` | `-V` | Show version |
| `--config` | `-c` | Config file path |
| `--verbose` | `-v` | Increase verbosity |
| `--quiet` | `-q` | Suppress output |
| `--no-color` | | Disable colors |
| `--json` | | JSON output |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AURORA_CONFIG` | Default config path |
| `AURORA_LOG_LEVEL` | Log level |
| `NO_COLOR` | Disable colors |

## Examples

```bash
aurora -v build          # Verbose
aurora -q run            # Quiet
aurora --json status     # JSON output
```

## See Also

- [Environment Variables](../13_configuration/environment_variables.md)
