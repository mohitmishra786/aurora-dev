# Capacity Planning

Predicting the future.

**Last Updated:** February 8, 2026
**Audience:** Architects

> **Before Reading This**
>
> You should understand:
> - [Scaling Guide](../08_deployment/scaling_guide.md)
> - [Performance Monitoring](./performance_monitoring.md)

## The Formula

`Required Compute = (RPS * Cost_Per_Req) / Target_Utilization`

If a Request takes 100ms (0.1s) of CPU time, 1 CPU core can handle 10 RPS.
To handle 1000 RPS, you need 100 cores.
Add buffer (keep utilization < 70%): You need 142 cores.

## Storage Growth

Monitor `disk_usage` slope.
If growing at 10GB/day, and you have 1TB free, you have 100 days until outage.
Set alerts at 80% usage to give time to procure more disk.

## Load Testing

Use `locust` to simulate traffic spikes.
Run a "Game Day" where you artificially create 10x load to see what breaks first (usually the DB).

## Related Reading

- [Scaling Guide](../08_deployment/scaling_guide.md)
- [Managing Costs](../05_user_guides/managing_costs.md)
