# Performance Monitoring

Watching the speedometer.

**Last Updated:** February 8, 2026
**Audience:** Performance Engineers

> **Before Reading This**
>
> You should understand:
> - [Monitoring Setup](./monitoring_setup.md)
> - [Benchmarks](../16_performance/benchmarks.md)

## APM (Application Performance Monitoring)

We recommend datadog or New Relic or OpenTelemetry.
These tools show the waterfall of a request:
`API (50ms) -> DB (200ms) -> External API (500ms)`.

## Latency Distributions

Averages hide lies. Look at Percentiles.
- **p50 (Median):** Typical user experience.
- **p95:** The slow users.
- **p99:** The outliers (often where the bugs live).

## Profiling in Production

Use `py-spy` to take a flamegraph of a running process without stopping it.
```bash
py-spy record -o profile.svg --pid 1234
```
This shows which functions are eating CPU.

## Related Reading

- [Performance Tuning](../06_developer_guides/performance_tuning.md)
- [Capacity Planning](./capacity_planning.md)
