# Docker Deployment

The universal container.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [System Requirements](../01_getting_started/system_requirements.md)
> - [Configuration](../13_configuration/environment_variables.md)

## The Dockerfile

We provide an optimized multi-stage build.
```dockerfile
# Stage 1: Build
FROM python:3.11-slim as builder
WORKDIR /app
COPY . .
RUN pip install .

# Stage 2: Runtime
FROM python:3.11-slim
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app
CMD ["aurora", "server"]
```

## Running with Compose

The easiest way to run production locally.

```bash
docker-compose up -d
```

This starts:
1. `aurora-server` (The API)
2. `postgres` (The DB)
3. `redis` (The Cache)
4. `qdrant` (The Vector DB)

## Environment Variables

Pass variables via `.env`.
```bash
docker run --env-file .env aurora/core:latest
```

## Volumes

Persist data by mounting volumes.
- `/var/lib/postgresql/data`
- `/app/.aurora` (Agent artifacts)

## Related Reading

- [Kubernetes Deployment](./kubernetes_deployment.md)
- [Self Hosted](./self_hosted.md)
