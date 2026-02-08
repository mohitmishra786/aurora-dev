# Rate Limits

Keeping the system stable.

**Last Updated:** February 8, 2026
**Audience:** Integrators

> **Before Reading This**
>
> You should understand:
> - [REST API](./rest_api.md)
> - [Error Codes](./error_codes.md)

## Default Limits

- **Global:** 1000 requests / minute per IP.
- **Agent Run:** 10 concurrent runs per User.
- **Memory Search:** 100 requests / second.

## Headers

We send standard headers:
- `X-RateLimit-Limit`: 1000
- `X-RateLimit-Remaining`: 999
- `X-RateLimit-Reset`: 1678900000 (Unix timestamp)

## 429 Too Many Requests

If you exceed the limit, you get a 429 status.
```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Retry in 60 seconds"
  }
}
```

## Handling Backoff

Clients should implement Exponential Backoff.
1. Wait 1s
2. Wait 2s
3. Wait 4s
4. Wait 8s

## Related Reading

- [Performance Tuning](../06_developer_guides/performance_tuning.md)
- [Queue Configuration](../13_configuration/queue_configuration.md)
