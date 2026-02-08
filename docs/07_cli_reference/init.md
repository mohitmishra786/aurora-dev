# CLI Reference: Init

Initialize a new AURORA-DEV project.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Synopsis

```bash
aurora init [OPTIONS] [NAME]
```

## Description

Creates a new AURORA-DEV project with the specified configuration.

## Arguments

| Argument | Description |
|----------|-------------|
| `NAME` | Project name (optional, prompts if not provided) |

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--template` | `-t` | Project template (fullstack, api, frontend, cli) |
| `--directory` | `-d` | Target directory (default: current) |
| `--no-git` | | Skip Git initialization |
| `--force` | `-f` | Overwrite existing directory |

## Examples

```bash
# Interactive setup
aurora init

# Quick start with template
aurora init my-app -t fullstack

# In specific directory
aurora init my-api -d ./projects -t api
```

## See Also

- [aurora build](./build.md)
- [aurora run](./run.md)
