# CLI Reference: Status

View project and agent status.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Synopsis

```bash
aurora status [OPTIONS]
```

## Description

Display current project status, active agents, and progress.

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--json` | `-j` | Output as JSON |
| `--watch` | `-w` | Live updates |
| `--tasks` | `-t` | Show task list |
| `--agents` | `-a` | Show agent details |

## Examples

```bash
# Quick status
aurora status

# Live dashboard
aurora status --watch

# JSON for scripts
aurora status --json

# With tasks
aurora status --tasks
```

## Output

```
Project: my-app
Status: IMPLEMENTING (65%)
Active: 3 agents
Tasks: 8/12 complete
Cost: $5.20
ETA: 10 min
```

## See Also

- [aurora logs](./logs.md)
- [aurora costs](./costs.md)
