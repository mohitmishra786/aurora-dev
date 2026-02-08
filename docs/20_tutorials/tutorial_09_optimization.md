# Tutorial 09: Optimization

Speeding it up.

**Last Updated:** February 8, 2026
**Difficulty:** Expert
**Time:** 20 mins

## Goal

Cache the `GET /tasks` endpoint using Redis.

## Step 1: Task Definition

```markdown
# Objective
Add `redis-py` dependency.
Update `main.py` to check Redis before querying the DB in `get_tasks`.
Invalidate the cache in `create_task`.
```

## Step 2: Run Agent

```bash
aurora run --task task.md --agent backend
```

## Step 3: Benchmark

Use `ab` (Apache Bench) to compare before/after.

## Next Step

[Tutorial 10: Advanced](./tutorial_10_advanced.md)
