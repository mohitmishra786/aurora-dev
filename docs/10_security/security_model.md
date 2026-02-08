# Security Model

Defense in Depth.

**Last Updated:** February 8, 2026
**Audience:** Security Engineers, Architects

> **Before Reading This**
>
> You should understand:
> - [Security Model Diagram](../21_diagrams/architecture/security_model.mmd)
> - [OWASP Compliance](./owasp_compliance.md)

## The Onion Architecture

We layer defenses. If one fails, the next catches the attack.

1. **Edge (WAF):** Cloudflare/AWS WAF. Blocks SQLi/XSS signatures.
2. **Network (VPC):** Private subnets. DB not accessible from internet.
3. **Application (Auth):** JWT verification on every request.
4. **Data (Encryption):** AES-256 at rest. TLS 1.3 in transit.
5. **Human (Audit):** Need-to-know access.

## Zero Trust

We do not trust the internal network. Service A must authenticate to talk to Service B (mTLS).
No "admin" VLANs that have open access.

## Threat Model

We assume:
- The attacker is inside the network.
- The attacker has stolen a user credential.
- The attacker has DOS capabilities.

We defend by:
- Short lived tokens (15 min).
- Rate limits.
- Anomaly detection (Login from new country).

## Related Reading

- [Authentication & Authorization](./authentication_authorization.md)
- [Compliance Checklist](../11_compliance/compliance_checklist.md)
