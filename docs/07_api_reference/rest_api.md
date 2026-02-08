# REST API Reference

The standard interface.

**Last Updated:** February 8, 2026
**Audience:** Integrators

> **Before Reading This**
>
> You should understand:
> - [Authentication](./authentication.md)
> - [Rate Limits](./rate_limits.md)

## Base URL

All URLs referenced in the documentation have the following base:
`https://api.aurora.dev/v1` (Production)
`http://localhost:8000/v1` (Local)

## Content-Type

The API accepts and returns `application/json`.
Exception: File uploads use `multipart/form-data`.

## Response Format

Success:
```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "total": 100
  }
}
```

Error:
```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Task 123 does not exist",
    "request_id": "req_abc123"
  }
}
```

## Idempotency

All `POST` requests support `Idempotency-Key` header.
If you retry a request with the same key, we return the cached response instead of creating a duplicate resource.

## Related Reading

- [Authentication](./authentication.md)
- [Error Codes](./error_codes.md)
