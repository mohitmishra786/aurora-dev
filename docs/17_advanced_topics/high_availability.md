# High Availability

Never say die.

**Last Updated:** February 8, 2026
**Audience:** SREs

> **Before Reading This**
>
> You should understand:
> - [Kubernetes Deployment](../08_deployment/kubernetes_deployment.md)
> - [Multi-Region](./multi_region.md)

## The 99.99% Architecture

- **Load Balancer:** Redundant (AWS ALB).
- **API Nodes:** Minimum 3 replicas across 3 Availability Zones (AZ).
- **Database:** RDS Multi-AZ. Active + Standby.

## Chaos Engineering

We use **Chaos Mesh** to randomly kill pods in production.
If the system works, the users notice nothing.

## Graceful Degradation

If the Vector DB is down:
- Application continues working but "Semantic Search" is disabled.
- Fallback to Keyword Search (Postgres).

## Related Reading

- [Multi-Region](./multi_region.md)
- [Incident Response](../09_operations/incident_response.md)
