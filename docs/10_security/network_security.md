# Network Security

Virtual walls.

**Last Updated:** February 8, 2026
**Audience:** Network Engineers

> **Before Reading This**
>
> You should understand:
> - [Security Model](./security_model.md)
> - [Infrastructure Diagram](../21_diagrams/architecture/infrastructure_diagram.mmd)

## Segmentation

- **Public Subnet:** Load Balancer, NAT Gateway.
- **Private Subnet:** App Servers.
- **Database Subnet:** DB, Redis. No Internet Gateway route.

## Security Groups

Allowlisting only.
- **LB:** Allow 443 from 0.0.0.0/0.
- **App:** Allow 8000 from LB SG.
- **DB:** Allow 5432 from App SG.

## mTLS (Mutual TLS)

Inside the cluster (e.g., using Istio), services authenticate each other with certificates.
This prevents a compromised container from scanning the internal network.

## Related Reading

- [Security Model](./security_model.md)
- [Certificate Management](../09_operations/certificate_management.md)
