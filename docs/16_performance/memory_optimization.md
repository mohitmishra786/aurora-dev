# Memory Optimization

Fitting in RAM.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Performance Problems](../14_troubleshooting/performance_problems.md)
> - [Redis Operations](../09_operations/redis_operations.md)

## Generators

Don't load 1GB CSVs into a list. Use generators.
```python
def read_lines(file):
    for line in file:
        yield line
```

## Slots

Use `__slots__` in Python classes to save memory per instance (removes the `__dict__` overhead).

## Rust Extensions

For critical paths, rewrite in Rust and bind via `PyO3`. We do this for the JSON parser.

## Related Reading

- [Performance Problems](../14_troubleshooting/performance_problems.md)
- [Performance Tuning](../06_developer_guides/performance_tuning.md)
