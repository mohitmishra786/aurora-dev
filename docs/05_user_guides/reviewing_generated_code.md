# Reviewing Generated Code

Best practices for validating AURORA-DEV output.

**Last Updated:** February 8, 2026  
**Audience:** Developers

## Review Checklist

Before deploying generated code:

- [ ] Review architecture decisions in `docs/architecture.md`
- [ ] Verify API contracts match expectations
- [ ] Run tests locally: `pytest --cov`
- [ ] Check security scan results
- [ ] Review database migrations
- [ ] Test critical user flows manually
- [ ] Verify environment configuration

## AI Code Review Report

AURORA provides its own review:

```markdown
## Code Review Summary

**Quality Score:** 8.5/10

### Strengths
- Clean separation of concerns
- Comprehensive test coverage (87%)
- Well-documented API

### Areas to Verify
1. `auth/jwt.py:45` - Token expiry should be configurable
2. `db/models.py:23` - Consider adding index for frequent query
3. `api/tasks.py:78` - Add rate limiting for this endpoint
```

## Manual Verification Focus Areas

| Area | Priority | Why |
|------|----------|-----|
| Authentication | High | Security critical |
| Data validation | High | Prevents corruption |
| Error handling | Medium | User experience |
| Performance | Medium | Scale issues |
| Edge cases | Low | AI may miss context |

## Related Reading

- [Code Reviewer Agent](../03_agent_specifications/12_code_reviewer.md)
- [Security Auditor](../03_agent_specifications/11_security_auditor.md)
