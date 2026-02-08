# Performance Tuning

Making it fly.

**Last Updated:** February 8, 2026
**Audience:** Performance Engineers

> **Before Reading This**
>
> You should understand:
> - [Performance Problems](../14_troubleshooting/performance_problems.md)
> - [Profiling Tools](../19_reference/resource_links.md)

## Profiling the Core

We use `cProfile` and `snakeviz` to analyze Python performance.
```bash
python -m cProfile -o profile.prof -m aurora run
snakeviz profile.prof
```

## Common Bottlenecks

### 1. Vector Search
Calculating cosine similarity on 1M vectors in Python is slow.
*Optimization:* Use HNSW libraries defined in Rust/C++ (e.g., `hnswlib`, `chromadb`).

### 2. JSON Serialization
The agents exchange massive JSON blobs. Standard `json` lib is slow.
*Optimization:* We use `orjson` which is 10x faster.

### 3. Tool Overhead
Starting a new `subprocess` for every CLI tool call is expensive.
*Optimization:* Use long-lived daemon processes or async I/O where possible.

## LLM Latency

The biggest bottleneck is the Model itself.
- **Streaming:** We stream tokens to the UI to improve Perceived Latency.
- **Speculative Decoding:** (Experimental) Predict the next few tokens locally to skip model usage.

## Related Reading

- [Performance Problems](../14_troubleshooting/performance_problems.md)
- [Managing Costs](../05_user_guides/managing_costs.md)
