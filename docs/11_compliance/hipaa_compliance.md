# HIPAA Compliance

Handling health data.

**Last Updated:** February 8, 2026
**Audience:** Healthcare Customers

> **Before Reading This**
>
> You should understand:
> - [Data Encryption](../10_security/data_encryption.md)
> - [Audit Trail](./audit_trail.md)

## BAA (Business Associate Agreement)

We sign a BAA with covered entities.
This creates legal liability for us if we leak PHI (Protected Health Information).

## Technical Safeguards

- **Access Control:** Unique user IDs. Automatic logoff.
- **Audit Controls:** We log *reads* of PHI, not just writes.
- **Integrity:** Digital signatures on medical records.
- **Transmission Security:** TLS 1.3 only.

## Dedicated Instances

For HIPAA customers, we often recommend the "Single Tenant" deployment option to physically isolate data.

## Related Reading

- [SOC2 Compliance](./soc2_compliance.md)
- [Data Encryption](../10_security/data_encryption.md)
