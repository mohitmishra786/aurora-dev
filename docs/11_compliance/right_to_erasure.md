# Right to Erasure

The right to be forgotten.

**Last Updated:** February 8, 2026
**Audience:** Support, Legal

> **Before Reading This**
>
> You should understand:
> - [GDPR Compliance](./gdpr_compliance.md)
> - [Data Retention](./data_retention.md)

## The Request

A user emails `privacy@aurora.dev` or clicks "Delete Account."
We have 30 days to comply.

## The Process

1. **Soft Delete:** Mark user as `deleted_at = NOW()`. They can no longer login.
2. **Grace Period:** Wait 30 days (in case of hacked account recovery).
3. **Hard Delete:**
   - Delete rows from Postgres (Cascading delete).
   - Delete vectors from Qdrant.
   - Delete files from S3.
   - Scrub logs (replace email with `[REDACTED]`).

## Exceptions

We do *not* delete:
- Billing records (required by law).
- Audit logs (required for security).
- Anonymized analytics data.

## Related Reading

- [Data Retention](./data_retention.md)
- [GDPR Compliance](./gdpr_compliance.md)
