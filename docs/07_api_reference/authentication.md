# Authentication

Identifying the caller.

**Last Updated:** February 8, 2026
**Audience:** Security Engineers

> **Before Reading This**
>
> You should understand:
> - [Security Model](../10_security/security_model.md)
> - [REST API](./rest_api.md)

## API Keys

For server-to-server communication, use API Keys.
Header: `Authorization: Bearer <API_KEY>`

Create a key:
```bash
aurora auth create-key --name "Production App"
```

## JWT (User Auth)

For frontend clients (Dashboard), use JWTs.
Flow:
1. `POST /auth/login` with username/password.
2. Receive `access_token` and `refresh_token`.
3. Send `access_token` in Header.

## Scopes

Keys can be scoped.
- `tasks:read`: Can view tasks.
- `tasks:write`: Can create tasks.
- `admin`: Can do everything.

## Revocation

You can revoke a key at any time:
`DELETE /auth/keys/{id}`

## Related Reading

- [Security Model](../10_security/security_model.md)
- [Rate Limits](./rate_limits.md)
