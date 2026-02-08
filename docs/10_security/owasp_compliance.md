# OWASP Compliance

Checking the boxes.

**Last Updated:** February 8, 2026
**Audience:** Security Auditors

> **Before Reading This**
>
> You should understand:
> - [Security Model](./security_model.md)
> - [Vulnerability Scanning](./vulnerability_scanning.md)

## OWASP Top 10 Mitigation

1. **Broken Access Control:** Enforced via RBAC middleware on every route.
2. **Cryptographic Failures:** We use Argon2id for hashing and TLS 1.3.
3. **Injection:** We use SQLAlchemy ORM (parameterized queries) preventing SQLi.
4. **Insecure Design:** Threat modeling performed at design phase.
5. **Security Misconfiguration:** Hardened Docker images used.
6. **Vulnerable Components:** Dependabot scans enabled.
7. **Auth Failures:** MFA enforced.
8. **Integrity Failures:** Signed commits and artifacts.
9. **Logging Failures:** Centralized logging with alerts.
10. **SSRF:** Network egress policies block access to metadata IP `169.254.169.254`.

## Related Reading

- [Vulnerability Scanning](./vulnerability_scanning.md)
- [Compliance Checklist](../11_compliance/compliance_checklist.md)
