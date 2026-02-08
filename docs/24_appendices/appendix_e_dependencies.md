# Appendix E: Dependencies

The software that powers the software builder.

**Last Updated:** February 8, 2026
**Audience:** Security Auditors

> **Before Reading This**
>
> You should understand:
> - [Installation](../01_getting_started/installation.md)

## Core Python Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| `anthropic` | ^0.18.0 | MIT | LLM Client |
| `fastapi` | ^0.109.0 | MIT | API Framework |
| `pydantic` | ^2.6.0 | MIT | Data Validation |
| `sqlalchemy`| ^2.0.0 | MIT | ORM |
| `asyncpg` | ^0.29.0 | Apache 2.0 | Async Postgres Driver |
| `redis` | ^5.0.0 | MIT | Queue Client |
| `typer` | ^0.9.0 | MIT | CLI Builder |
| `rich` | ^13.7.0 | MIT | Terminal UI |

## Development Tools

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | ^8.0.0 | Testing |
| `ruff` | ^0.2.0 | Linting (Fast) |
| `black` | ^24.0.0 | Formatting |
| `mypy` | ^1.8.0 | Type Checking |
| `pre-commit` | ^3.6.0 | Git Hooks |

## System Requirements

- **Python:** 3.10+
- **Docker:** 24.0+
- **Node.js:** 18+ (Optional, for frontend tasks)

## Related Reading

- [Installation Guide](../01_getting_started/installation.md)
