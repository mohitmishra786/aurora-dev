# CLI Reference: Logs

View agent and system logs.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Synopsis

```bash
aurora logs [OPTIONS]
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--agent` | `-a` | Filter by agent |
| `--task` | `-t` | Filter by task ID |
| `--follow` | `-f` | Stream live logs |
| `--lines` | `-n` | Number of lines |
| `--level` | `-l` | Min log level |

## Examples

```bash
aurora logs               # All logs
aurora logs -f            # Follow live
aurora logs -a backend    # Backend only
aurora logs -n 50         # Last 50 lines
aurora logs -l error      # Errors only
```

## See Also

- [aurora status](./status.md)
