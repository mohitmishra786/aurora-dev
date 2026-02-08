# Scaling Strategies

Horizontal and vertical scaling for AURORA-DEV.

**Last Updated:** February 8, 2026  
**Audience:** DevOps Engineers

## Horizontal Scaling

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aurora-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aurora
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## Component Scaling

| Component | Scaling Method |
|-----------|----------------|
| API servers | Horizontal (stateless) |
| Workers | Horizontal |
| PostgreSQL | Vertical + Read replicas |
| Redis | Cluster mode |

## Load Testing

```bash
locust -f load_test.py --host http://aurora:8000
```

## Related Reading

- [Performance Tuning](../16_performance/performance_tuning.md)
