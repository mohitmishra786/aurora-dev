# Case Study: REST API Project

Building a bank from scratch.

**Last Updated:** February 8, 2026
**Industry:** Fintech

## Challenge

Startup "NeoBank" needed a PCI-compliant API to handle ledger transactions. Strict requirement: 100% test coverage and audit logs for everything.

## Solution

We used the **Backend Agent** with a custom "Security First" system prompt.
1. **Model:** `claude-3-opus` for all code generation (to minimize vulnerabilities).
2. **Review:** **Security Auditor Agent** configured to block any PR with missing `AuditLog` calls.

## Results

- **Velocity:** 50 endpoints delivered in 4 weeks.
- **Compliance:** Passed external penetration test with 0 critical findings.

## Key Learnings

- **Strict Types:** Using Pydantic models for everything prevented a class of injection attacks.
- **Documentation:** The **Documentation Agent** automatically kept the OpenAPI spec in sync with the code, which pleased the auditors.

## Related Reading

- [API Security](../10_security/api_security.md)
- [Audit Trail](../11_compliance/audit_trail.md)
