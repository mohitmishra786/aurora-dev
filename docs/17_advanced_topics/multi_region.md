# Multi-Region Deployment

Global domination.

**Last Updated:** February 8, 2026
**Audience:** SREs

> **Before Reading This**
>
> You should understand:
> - [Cloud AWS](../08_deployment/cloud_aws.md)
> - [Disaster Recovery](../08_deployment/disaster_recovery.md)

## Active-Passive

- **Primary:** `us-east-1` (Read/Write)
- **Secondary:** `eu-west-1` (Read Only)
- **Replication:** Postgres Streaming Replication.
- **Failover:** Manual promotion (RTO 5 mins).

## Active-Active (Global Tables)

For purely stateless workloads, you can run active nodes in both regions.
State (DB) is the hard part.
We recommend **CockroachDB** or **DynamoDB Global Tables** if you need multi-master writes.

## Latency Routing

Use AWS Route53 "Latency Based Routing".
Users in London are routed to `eu-west-1`.
Users in New York are routed to `us-east-1`.

## Related Reading

- [Disaster Recovery](../08_deployment/disaster_recovery.md)
- [High Availability](./high_availability.md)
