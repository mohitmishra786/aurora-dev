# Parallel Execution

Doing two things at once.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Task Decomposition](../04_core_concepts/task_decomposition.md)
> - [Optimization Techniques](./optimization_techniques.md)

## CPU Bound vs I/O Bound

- **CPU Bound (Math, Parsing):** Use `multiprocessing`. Python GIL limits threads.
- **I/O Bound (API, DB):** Use `asyncio` or `threading`.

## The `TaskExecutor`

Our core engine uses a generic executor.
```python
with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(fetch_url, urls))
```

## Safety

Parallel code introduces Race Conditions.
Always use `locks` when modifying shared state.
Prefer "Shared Nothing" architecture where workers don't touch common globals.

## Related Reading

- [Task Decomposition](../04_core_concepts/task_decomposition.md)
- [Performance Tuning](../06_developer_guides/performance_tuning.md)
