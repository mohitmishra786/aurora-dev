# API Errors

500 Internal Server Error.

**Last Updated:** February 8, 2026
**Audience:** Integrators

> **Before Reading This**
>
> You should understand:
> - [Error Codes](../07_api_reference/error_codes.md)
> - [Logging Setup](../09_operations/logging_setup.md)

## 502 Bad Gateway

*Cause:* The `aurora-server` is down, but Nginx is up.
*Fix:* Restart the backend container. Check logs for crash on startup.

## 504 Gateway Timeout

*Cause:* The request took > 60s.
*Fix:* Use the Async API (`POST /tasks`). Do not wait for long jobs synchronously.

## CORS Error

*Cause:* Frontend domain not in `ALLOWED_ORIGINS`.
*Fix:* Update `aurora.yaml` to include `https://your-domain.com`.

## Related Reading

- [Error Codes](../07_api_reference/error_codes.md)
- [Network Issues](./network_issues.md)
