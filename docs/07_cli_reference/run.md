# CLI Reference: Run

Execute a specific agent or workflow phase.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Synopsis

```bash
aurora run [OPTIONS] [PHASE]
```

## Description

Run a specific phase or resume from a checkpoint.

## Arguments

| Argument | Description |
|----------|-------------|
| `PHASE` | Optional phase: plan, implement, test, review, deploy |

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--agent` | `-a` | Run specific agent only |
| `--task` | `-t` | Run specific task ID |
| `--resume` | `-r` | Resume from checkpoint |
| `--watch` | `-w` | Watch mode with live output |

## Examples

```bash
# Run full pipeline
aurora run

# Planning only
aurora run plan

# Resume interrupted build
aurora run --resume

# Run single agent
aurora run -a backend

# Watch mode
aurora run --watch
```

## See Also

- [aurora build](./build.md)
- [aurora status](./status.md)
