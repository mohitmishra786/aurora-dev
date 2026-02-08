# Authentication & Authorization

Who are you and what can you do?

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Security Model](./security_model.md)
> - [API Security](./api_security.md)

## Identity Provider (IdP)

We outsource Identity to Auth0 or Cognito or Keycloak.
We do not store passwords. We store OIDC metadata.

## RBAC (Role Based Access Control)

Users have Roles. Roles (not users) have Permissions.
- **Admin:** `*`
- **Editor:** `task:create`, `task:edit`
- **Viewer:** `task:read`

Policy code:
```python
def check_permission(user, permission):
    if permission in user.role.permissions:
        return True
    raise Forbidden()
```

## Service Accounts

Robots use API Keys. These keys map to a specific "Bot User" with specific scopes.
Never use a human's credential for a cron job.

## Related Reading

- [API Security](./api_security.md)
- [Secrets Management](./secrets_management.md)
