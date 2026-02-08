# Deploying to AWS

The cloud native way.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Kubernetes Deployment](./kubernetes_deployment.md)
> - [AWS Services](../12_integration/aws_services.md)

## Architecture

Recommended setup:
- **Compute:** EKS (Elastic Kubernetes Service)
- **Database:** RDS (PostgreSQL 15+)
- **Cache:** ElastiCache (Redis)
- **Vectors:** OpenSearch or self-hosted Qdrant on EC2.

## Terraform

We provide Terraform modules in `deploy/terraform/aws`.

```hcl
module "aurora" {
  source = "./modules/aurora"
  vpc_id = module.vpc.vpc_id
  db_endpoint = module.db.endpoint
}
```

## IAM Roles

Use IRSA (IAM Roles for Service Accounts).
- `aurora-backend` role needs access to:
  - S3 (Artifact storage)
  - Bedrock (If using AWS models)

## Cost Estimation

For a small team (5 devs):
- t3.medium nodes (x2): $60/mo
- RDS db.t3.micro: $15/mo
- ElastiCache: $15/mo
Total: ~$100/mo + API Usage.

## Related Reading

- [Scaling Guide](./scaling_guide.md)
- [Backup & Restore](./backup_restore.md)
