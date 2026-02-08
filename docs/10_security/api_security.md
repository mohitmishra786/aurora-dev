# API Security

Locking the front door.

**Last Updated:** February 8, 2026
**Audience:** Backend Developers

> **Before Reading This**
>
> You should understand:
> - [Authentication](./authentication_authorization.md)
> - [Rate Limits](../07_api_reference/rate_limits.md)

## Input Validation

Trust no one.
Every endpoint uses Pydantic models to strictly define expected types and constraints.
```python
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-z0-9]+$")
```

## Output Sanitization

Never return internal objects directly.
Use response models to strip `password_hash` and `internal_id` from the JSON response.

## CORS

Only allow trusted origins.
`Access-Control-Allow-Origin: https://dashboard.aurora.dev`
Do not use `*`.

## Rate Limiting

See [Rate Limits](../07_api_reference/rate_limits.md).
We implement limits by IP Key and User ID to prevent DOS.

## Related Reading

- [Authentication](./authentication_authorization.md)
- [OWASP Compliance](./owasp_compliance.md)
