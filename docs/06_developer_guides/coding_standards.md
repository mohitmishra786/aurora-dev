# Coding Standards

The law of the land.

**Last Updated:** February 8, 2026
**Audience:** All Developers

> **Before Reading This**
>
> You should understand:
> - [Contributing](./contributing.md)
> - [Code Reviewer](../03_agent_specifications/12_code_reviewer.md)

## Python

We follow **PEP 8** with modifications.

- **Line Length:** 88 characters (Black default).
- **Type Hints:** Required for all function arguments and returns.
- **Docstrings:** Google Style.

```python
def calculate_velocity(dist: float, time: float) -> float:
    """Calculates velocity.

    Args:
        dist: Distance in meters.
        time: Time in seconds.

    Returns:
        Velocity in m/s.
    """
    return dist / time
```

## TypeScript / JavaScript

We follow **Airbnb Style Guide**.

- **Semicolons:** Always.
- **Quotes:** Single quotes preferred.
- **Async/Await:** Preferred over Promises.

## Git Commits

We follow **Conventional Commits**.

- `feat: add user login`
- `fix: resolve crash on startup`
- `docs: update readme`
- `chore: bump dependencies`

## Directory Structure

- `src/core`: Business logic (Pure Python).
- `src/api`: HTTP layer (FastAPI).
- `src/db`: Database models (SQLAlchemy).

Do not import `api` code into `core`. Dependencies should flow one way: `API -> Core -> DB`.

## Related Reading

- [Code Reviewer](../03_agent_specifications/12_code_reviewer.md)
- [Contributing](./contributing.md)
