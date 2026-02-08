# Optimization Techniques

Squeezing the lemon.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Benchmarks](./benchmarks.md)
> - [Profiling Tools](../19_reference/resource_links.md)

## Algorithm Optimization

Don't use O(N^2) when O(N) will do.
*Bad:* Nested loops over lists.
*Good:* Convert list to set/dict for O(1) lookup.

## Database Tuning

1. **Select Fields:** Only fetch columns you need. `SELECT id, name` not `SELECT *`.
2. **N+1 Problem:** Use `.options(selectinload(User.posts))` to fetch related data in 1 query.

## Async I/O

Python is single-threaded. Blocking I/O kills performance.
Always use `await` for:
- DB calls.
- API calls.
- File reads.

## Related Reading

- [Database Optimization](./database_optimization.md)
- [Caching Strategies](./caching_strategies.md)
