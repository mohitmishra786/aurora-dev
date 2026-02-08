# Load Testing

Breaking it on purpose.

**Last Updated:** February 8, 2026
**Audience:** QA, SREs

> **Before Reading This**
>
> You should understand:
> - [Benchmarks](./benchmarks.md)
> - [Capacity Planning](../09_operations/capacity_planning.md)

## Tools

We use **Locust**. It allows writing test scenarios in Python.

```python
class WebsiteUser(HttpUser):
    @task
    def index(self):
        self.client.get("/")
    
    @task(3)
    def view_item(self):
        self.client.get(f"/item/{random.randint(1, 100)}")
```

## Methodology

1. **Baseline:** 1 user. Verify functionality.
2. **Ramp:** 1 -> 1000 users over 10 minutes.
3. **Soak:** Maintain 1000 users for 1 hour (finds memory leaks).
4. **Spike:** Jump to 5000 users instantly (finds concurrency bugs).

## Analysis

Look for the "Knee of the Curve" where latency spikes exponentially. That is your capacity limit.

## Related Reading

- [Capacity Planning](../09_operations/capacity_planning.md)
- [Benchmarks](./benchmarks.md)
