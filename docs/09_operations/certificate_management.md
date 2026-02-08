# Certificate Management

Keeping the lock icon green.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Network Security](../10_security/network_security.md)
> - [Kubernetes Deployment](../08_deployment/kubernetes_deployment.md)

## Cert-Manager

In Kubernetes, use `cert-manager`.
It automates Let's Encrypt issuance.

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
```

## Manual Renewal

If running on bare metal with Nginx:
`certbot --nginx -d aurora.example.com`
This adds a cron job to auto-renew.

## Internal CA

For service-to-service mTLS, use a private CA (e.g., Hashicorp Vault).
Do not use self-signed certs without a root CA, or agents will throw SSL verification errors.

## Related Reading

- [Network Security](../10_security/network_security.md)
- [Security Model](../21_diagrams/architecture/security_model.mmd)
