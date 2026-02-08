# Common Errors

The greatest hits.

**Last Updated:** February 8, 2026
**Audience:** All Users

> **Before Reading This**
>
> You should understand:
> - [Error Codes](../07_api_reference/error_codes.md)
> - [Debugging Failures](../05_user_guides/debugging_failures.md)

## `401 Unauthorized`

- **Cause:** API Key missing or invalid.
- **Fix:** Check headers. Regenerate key.

## `connection refused`

- **Cause:** Database or Redis is not running.
- **Fix:** `docker-compose up -d`. Check logs.

## `context length exceeded`

- **Cause:** You fed the agent a 2MB file.
- **Fix:** Use smaller files. Ignore `node_modules`.

## `agent stuck in loop`

- **Cause:** Agent keeps trying to read a file that doesn't exist.
- **Fix:** Edit the file manually. Give the agent a hint.

## `out of memory`

- **Cause:** Loading 1M rows into Python list.
- **Fix:** Use pagination.

## Related Reading

- [Error Codes](../07_api_reference/error_codes.md)
- [Agent Failures](./agent_failures.md)
