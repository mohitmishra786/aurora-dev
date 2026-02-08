# Tutorial 04: Testing

Ensuring it works.

**Last Updated:** February 8, 2026
**Difficulty:** Intermediate
**Time:** 10 mins

## Goal

Write unit tests for the FastAPI backend using `pytest`.

## Step 1: Task Definition

```markdown
# Objective
Write unit tests for `main.py` using `pytest` and `TestClient`.
Cover all 4 endpoints (GET, POST, PUT, DELETE).
Save tests to `tests/test_main.py`.
```

## Step 2: Run Agent

```bash
aurora run --task task.md --agent test_engineer
```

## Step 3: Run Tests

```bash
pytest
```

## Next Step

[Tutorial 05: Deployment](./tutorial_05_deployment.md)
