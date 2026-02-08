# Integration Problems

Troubleshooting third-party integrations.

**Last Updated:** February 8, 2026  
**Audience:** Developers

## GitHub Issues

### Authentication Failed
```bash
# Verify token
gh auth status

# Regenerate token with correct scopes
```

Required scopes: `repo`, `workflow`

### Push Rejected
Check branch protection rules and CODEOWNERS file.

## Slack Issues

### Webhook Not Receiving
1. Verify webhook URL is accessible
2. Check Slack app permissions
3. Test with curl:
```bash
curl -X POST $SLACK_WEBHOOK -d '{"text":"test"}'
```

## Database Issues

### Connection Refused
```bash
# Check PostgreSQL is running
pg_isready -h localhost

# Verify credentials
psql $DATABASE_URL -c "SELECT 1"
```

## Related Reading

- [Custom Integrations](../12_integration/custom_integrations.md)
