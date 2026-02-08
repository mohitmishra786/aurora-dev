# Benchmarks

Faster than light.

**Last Updated:** February 8, 2026
**Audience:** Architects

> **Before Reading This**
>
> You should understand:
> - [Performance Monitoring](../09_operations/performance_monitoring.md)
> - [Load Testing](./load_testing.md)

## RPS (Requests Per Second)

Tested on AWS `c6i.xlarge` (4 vCPU, 8GB RAM).

| Endpoint | RPS | Latency (p99) |
|----------|-----|---------------|
| `GET /health` | 12,000 | 2ms |
| `GET /tasks` | 2,500 | 45ms |
| `POST /agent/run` | 50 | 5,000ms (LLM bound) |

## Database Throughput

Postgres 15 on `db.m6g.xlarge`.
- **Write:** 5,000 inserts/sec.
- **Read:** 50,000 selects/sec.

## Vector Search

Qdrant on `r6g.xlarge`.
- **Collection:** 1M vectors (1536 dim).
- **Search:** 15ms latency.

## Related Reading

- [Load Testing](./load_testing.md)
- [Optimization Techniques](./optimization_techniques.md)
