# Development Setup

Building the builder.

**Last Updated:** February 8, 2026
**Audience:** Contributors, Plugin Developers

> **Before Reading This**
>
> You should understand:
> - [System Requirements](../01_getting_started/system_requirements.md)
> - [Project Structure](./project_structure.md)

## Prerequisites

To hack on the AURORA-DEV core, you need a robust environment.

- **Python 3.10+**: We use strict type hinting.
- **Poetry**: For dependency management.
- **Docker**: For running integration tests.
- **Node.js 18+**: For the dashboard frontend.

## Installation

1. **Clone the Repo:**
   ```bash
   git clone https://github.com/aurora-dev/core.git
   cd core
   ```

2. **Install Dependencies:**
   ```bash
   poetry install
   pre-commit install
   ```

3. **Configure Environment:**
   Copy `.env.example` to `.env`.
   Add your `ANTHROPIC_API_KEY`.

## Running Locally

We use a `Makefile` to simplify commands.

- `make lint`: Run ruff and black.
- `make test`: Run unit tests.
- `make dev`: Start the backend in hot-reload mode.

## Architecture Overview

The core logic resides in `aurora/core/`.
- `agents/`: The Agent classes (BaseAgent, BackendAgent).
- `memory/`: Vector DB wrappers (Chroma/Qdrant).
- `tools/`: The tool definitions (FileRead, ShellRun).

## Debugging

We recommend using VS Code. The `.vscode/launch.json` is pre-configured to attach to the running process. Simple press `F5` to start debugging.

## Submitting a PR

1. Create a branch: `feat/my-cool-feature`.
2. Write code + tests.
3. Verify: `make check` (runs lint + test + type check).
4. Push and open PR.

## Related Reading

- [Coding Standards](./coding_standards.md)
- [Contributing](./contributing.md)
