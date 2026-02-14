# Codebase Explorer

Proactive codebase scanning for agent context awareness.

**Last Updated:** February 14, 2026  
**Audience:** Developers, AI Engineers

> **Before Reading This**
>
> You should understand:
> - [Context Management](../04_core_concepts/context_management.md) - Retrieval strategies
> - [Base Agent](../03_agent_specifications/00_base_agent.md) - Agent execution flow

## Overview

The `CodebaseExplorer` (`aurora_dev/tools/codebase_explorer.py`) gives agents proactive awareness of existing code patterns, conventions, and utilities before they start modifying code. Instead of agents writing code "blind," they first scan the codebase for relevant prior art.

## Problem It Solves

Without codebase awareness, agents frequently:
- Reinvent utilities that already exist
- Break existing patterns by introducing inconsistent approaches
- Duplicate auth/validation/error-handling logic
- Use different naming conventions than the rest of the project

## Architecture

```mermaid
graph LR
    A[Agent receives task<br/>"Add rate limiting"] --> CE[CodebaseExplorer]
    CE -->|git ls-files| F[Find relevant files]
    F --> P[Extract patterns<br/>& conventions]
    P --> I[CodebaseInsight]
    I --> A
    A --> C[Generate code<br/>following patterns]
```

## Key Features

### Polyglot Support

The explorer supports multiple languages out of the box. Extensions are configurable per-project:

| Language | Default Extensions |
|----------|--------------------|
| Python | `.py` |
| TypeScript/JavaScript | `.ts`, `.js`, `.tsx`, `.jsx` |
| Go | `.go` |
| Rust | `.rs` |
| Java/Kotlin | `.java`, `.kt` |
| Config | `.yaml`, `.yml`, `.toml` |
| Docker | `.dockerfile`, `.Dockerfile` |

Override via constructor:

```python
explorer = CodebaseExplorer(
    repo_path="/path/to/project",
    extensions=[".py", ".go", ".proto"],  # Custom set
)
```

### Language-Agnostic File Discovery

Uses a three-tier file discovery approach:

1. **`git ls-files`** (primary) — Respects `.gitignore`, works across all languages
2. **`grep -rl`** (fallback) — When not in a git repo, uses dynamic `--include` flags
3. **Directory walk** (last resort) — `os.walk` with smart directory exclusion

### Smart Directory Exclusion

Automatically skips noise directories:

```python
IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv",
    "venv", ".tox", ".mypy_cache", "dist", "build",
}
```

## API

```python
from aurora_dev.tools.codebase_explorer import CodebaseExplorer

explorer = CodebaseExplorer(repo_path="/path/to/project")

# Explore a topic
insights = await explorer.explore(
    topic="authentication",
    max_files=10,
    file_extensions=[".py", ".ts"],  # Optional override
)

for insight in insights:
    print(f"File: {insight.file_path}")
    print(f"Patterns: {insight.patterns}")
    print(f"Conventions: {insight.conventions}")
```

### CodebaseInsight

Each insight contains:

| Field | Description |
|-------|-------------|
| `file_path` | Path to the relevant file |
| `patterns` | Detected code patterns (error handling, auth, etc.) |
| `conventions` | Naming conventions and coding style |
| `utilities` | Existing helper functions that could be reused |
| `imports` | Key imports used in the file |

## Caching

Results are cached by topic to avoid repeated file system scans within the same session:

```python
# First call: scans filesystem
insights = await explorer.explore("database")  # ~200ms

# Second call: returns cached results
insights = await explorer.explore("database")  # ~0ms
```

## Related Reading

- [Context Management](../04_core_concepts/context_management.md) - How context feeds into agents
- [Base Agent](../03_agent_specifications/00_base_agent.md) - Agent execution lifecycle
- [Agent Assignment](../04_core_concepts/agent_assignment.md) - How agents are selected

## What's Next

- [Budget Manager](./budget_manager.md) - Token cost controls
