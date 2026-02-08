# CLI Reference: Export

Export project artifacts.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Synopsis

```bash
aurora export [OPTIONS] [OUTPUT]
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--format` | `-f` | Output format (zip, tar.gz) |
| `--include` | `-i` | Include (code, tests, docs, all) |
| `--exclude` | `-e` | Exclude patterns |

## Examples

```bash
aurora export                    # Export all
aurora export -f zip output.zip  # As zip
aurora export -i code,tests      # Code and tests only
aurora export -e "*.log"         # Exclude logs
```

## See Also

- [aurora build](./build.md)
