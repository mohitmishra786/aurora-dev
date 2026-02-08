# Secrets Management

Keeping secrets secret.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Security Model](./security_model.md)
> - [Configuration](../13_configuration/environment_variables.md)

## The Rules

1. **No git:** Never commit secrets to the repo. Scan for them in CI.
2. **No env vars:** Env vars can leak in logs. Use volume mounts if possible.
3. **Rotation:** Change keys every 90 days.

## Vault Integration

We integrate with HashiCorp Vault.
At startup, `aurora-server` authenticates to Vault, reads secrets into memory, and keeps them there. Not on disk.

## Kubernetes Secrets

If not using Vault, use K8s Secrets encrypted at rest.
Use `ExternalSecrets` operator to sync from AWS Secrets Manager to K8s.

## Related Reading

- [Configuration](../13_configuration/environment_variables.md)
- [Data Encryption](./data_encryption.md)
