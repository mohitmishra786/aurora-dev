# Cloud Deployment

Deploying to AWS, GCP, and Azure.

**Last Updated:** February 8, 2026  
**Audience:** DevOps Engineers

## AWS (ECS)

```bash
# Create cluster
aws ecs create-cluster --cluster-name aurora

# Deploy service
aws ecs create-service \
  --cluster aurora \
  --service-name aurora-service \
  --task-definition aurora-task \
  --desired-count 2
```

## GCP (Cloud Run)

```bash
gcloud run deploy aurora \
  --image ghcr.io/aurora-dev/aurora-dev:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
```

## Azure (Container Apps)

```bash
az containerapp create \
  --name aurora \
  --resource-group aurora-rg \
  --environment aurora-env \
  --image ghcr.io/aurora-dev/aurora-dev:latest \
  --cpu 1 --memory 2.0Gi \
  --ingress external --target-port 8000
```

## Managed Services

Use cloud-managed services for:
- PostgreSQL (RDS, Cloud SQL, Azure Database)
- Redis (ElastiCache, Memorystore, Cache for Redis)

## Related Reading

- [Kubernetes Deployment](./kubernetes_deployment.md)
- [Environment Variables](../13_configuration/environment_variables.md)
