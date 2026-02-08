# Kubernetes Deployment

Orchestrating the orchestra.

**Last Updated:** February 8, 2026
**Audience:** SREs

> **Before Reading This**
>
> You should understand:
> - [Docker Deployment](./docker_deployment.md)
> - [Infrastructure Diagram](../21_diagrams/architecture/infrastructure_diagram.mmd)

## Helm Chart

We provide an official Helm chart.
```bash
helm repo add aurora https://charts.aurora.dev
helm install my-aurora aurora/core
```

## Manifests

If you prefer raw YAML:

### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aurora-server
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: core
          image: aurora/core:latest
          envFrom:
            - secretRef:
                name: aurora-secrets
```

### Service
Expose port 8000 via a LoadBalancer or Ingress.

## Scalability

Use HPA (Horizontal Pod Autoscaler).
Target CPU utilization: 70%.
Aurora is stateless (mostly), so scaling is linear.

## Persistence

Use PVCs for:
- Database (if running in-cluster, which is not recommended for prod).
- Agent Artifacts (Use S3 instead).

## Related Reading

- [Scaling Guide](./scaling_guide.md)
- [Cloud AWS](./cloud_aws.md)
