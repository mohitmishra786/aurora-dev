# Appendix D: Network Ports

Start your firewalls.

**Last Updated:** February 8, 2026
**Audience:** DevOps Engineers

> **Before Reading This**
>
> You should understand:
> - [Docker Deployment](../08_deployment/docker_deployment.md)

## Standard Ports

These are the ports used by the `docker-compose.yml` stack.

| Service | Internal Port | Host Port | Protocol | Description |
|---------|---------------|-----------|----------|-------------|
| **API** | 8000 | 8000 | HTTP | Main REST API |
| **Frontend** | 3000 | 3000 | HTTP | React Dev Server |
| **PostgreSQL** | 5432 | 5432 | TCP | Database |
| **Redis** | 6379 | 6379 | TCP | Cache/Queue |
| **Adminer** | 8080 | 8080 | HTTP | DB GUI |
| **Prometheus**| 9090 | 9090 | HTTP | Metrics Scraper |
| **Grafana** | 3001 | 3001 | HTTP | Dashboards |
| **Mem0** | 8081 | 8081 | HTTP | Vector Store API |

## Changing Ports

To avoid port conflicts, set environment variables in `.env`:

```bash
AURORA_API_PORT=8001
AURORA_DB_PORT=5433
```

## Firewall Rules

**Inbound:**
- Allow 80/443 (HTTP/HTTPS) for public access.
- Allow 22 (SSH) for admin access.
- Block all others.

**Outbound:**
- Allow 443 (HTTPS) to `api.anthropic.com`.
- Allow 443 (HTTPS) to `pypi.org`, `npmjs.com` (for package installs).

## Related Reading

- [Security Model](../10_security/security_model.md)
