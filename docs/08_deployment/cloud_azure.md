# Deploying to Azure

Enterprise grade.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Kubernetes Deployment](./kubernetes_deployment.md)
> - [Authentication](../10_security/authentication_authorization.md)

## Components

- **Compute:** AKS (Azure Kubernetes Service).
- **Database:** Azure Database for PostgreSQL - Flexible Server.
- **Cache:** Azure Cache for Redis.
- **AI:** Azure OpenAI Service.

## Deployment Script

Use Bicep templates located in `deploy/azure`.

```bash
az deployment group create --resource-group aurora-rg --template-file main.bicep
```

## Azure AD Integration

For internal dashboards, we recommend using Azure AD (Entra ID) for authentication instead of basic auth.
Set `AUTH_PROVIDER=azure_ad` in `aurora.yaml`.

## Key Vault

Store secrets in Key Vault and use the "Secrets Store CSI Driver" to mount them into pods.

## Related Reading

- [Cloud GCP](./cloud_gcp.md)
- [Upgrade Guide](./upgrade_guide.md)
