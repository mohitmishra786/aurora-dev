# CLI Reference: Costs

View and manage API usage costs.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Synopsis

```bash
aurora costs [OPTIONS]
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--daily` | `-d` | Daily breakdown |
| `--weekly` | `-w` | Weekly summary |
| `--project` | `-p` | By project |
| `--model` | `-m` | By model |

## Examples

```bash
aurora costs              # Current session
aurora costs --daily      # Today's costs
aurora costs -p my-app    # By project
aurora costs --model      # By AI model
```

## See Also

- [Managing Costs](../05_user_guides/managing_costs.md)
