# Project Structure

The anatomy of the codebase.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Project Template](../22_templates/project_template.md)
> - [Development Setup](./development_setup.md)

## The Monorepo Layout

We use a monorepo structure to keep everything in sync.

```
/
├── docs/                   # You are here
├── src/
│   ├── aurora/             # Core Python package
│   │   ├── agents/         # Brains
│   │   ├── tools/          # Hands
│   │   └── memory/         # Storage
│   │
│   └── dashboard/          # Next.js Web UI
│       ├── components/
│       └── pages/
│
├── tests/                  # Pytest suite
├── plugins/                # Bundled plugins
├── scripts/                # CI/CD helpers
├── poetry.lock             # Python deps
└── package.json            # JS deps
```

## Key Files

- `pyproject.toml`: The source of truth for Python dependencies and tool configs (ruff, mypy, pytest).
- `aurora.yaml`: The default configuration file loaded by the CLI.
- `Makefile`: Shortcuts for common tasks.

## Why this structure?

1. **Collocation:** Agents logic and the Dashboard UI often change together. Keeping them close reduces context switching.
2. **Unified Git History:** Atomic commits that span backend and frontend.
3. **Simplified CI:** One pipeline to build everything.

## Related Reading

- [Project Template](../22_templates/project_template.md)
- [Development Setup](./development_setup.md)
