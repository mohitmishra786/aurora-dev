# Data Encryption

Protecting the crown jewels.

**Last Updated:** February 8, 2026
**Audience:** Compliance Officers

> **Before Reading This**
>
> You should understand:
> - [Secrets Management](./secrets_management.md)
> - [Compliance Checklist](../11_compliance/compliance_checklist.md)

## At Rest

- **Database:** Disk encryption (e.g., AWS EBS encryption).
- **Backups:** S3 Bucket Encryption (SSE-S3 or KMS).
- **Application Level:** Sensitive fields (SSN, API Keys) are encrypted *inside* the DB row using `fernet` (symmetric).

## In Transit

- **External:** TLS 1.2 or 1.3 enforced. HSTS header set.
- **Internal:** TLS between load balancer and target.

## Key Management

We use a Master Key (KMS) to encrypt Data Keys.
This allows us to rotate the master key without re-encrypting terabytes of data (Envelope Encryption).

## Related Reading

- [Secrets Management](./secrets_management.md)
- [GDPR Compliance](../11_compliance/gdpr_compliance.md)
