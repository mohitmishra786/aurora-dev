# Authentication Setup

Configuring authentication for AURORA-DEV.

**Last Updated:** February 8, 2026  
**Audience:** Security Engineers

## JWT Configuration

```yaml
auth:
  jwt:
    secret: ${JWT_SECRET}  # Min 256 bits
    algorithm: HS256
    access_token_ttl: 900  # 15 minutes
    refresh_token_ttl: 604800  # 7 days
```

## API Key Authentication

```python
@router.get("/api/projects", dependencies=[Depends(verify_api_key)])
async def list_projects():
    pass
```

## OAuth2 (Optional)

```yaml
oauth:
  google:
    client_id: ${GOOGLE_CLIENT_ID}
    client_secret: ${GOOGLE_CLIENT_SECRET}
  github:
    client_id: ${GITHUB_CLIENT_ID}
    client_secret: ${GITHUB_CLIENT_SECRET}
```

## SSO Integration

SAML and OIDC supported for enterprise deployments.

## Related Reading

- [Security Model](./security_model.md)
- [API Security](./api_security.md)
