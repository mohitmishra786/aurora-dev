# CLI Reference: Build

Generate code from project specification.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Synopsis

```bash
aurora build [OPTIONS]
```

## Description

Executes the full AURORA-DEV pipeline: planning, implementation, testing, and review.

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Path to aurora.yaml |
| `--skip-tests` | | Skip test generation |
| `--skip-docs` | | Skip documentation |
| `--dry-run` | | Plan only, no code changes |
| `--parallel` | `-p` | Max parallel agents (default: 4) |
| `--budget` | `-b` | Max cost in USD |

## Examples

```bash
# Full build
aurora build

# Planning only
aurora build --dry-run

# With budget limit
aurora build --budget 50

# Maximum parallelism
aurora build -p 8
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Build failed |
| 2 | Budget exceeded |
| 130 | User cancelled |

## See Also

- [aurora run](./run.md)
- [aurora status](./status.md)
