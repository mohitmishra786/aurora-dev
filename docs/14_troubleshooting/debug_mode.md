# Debug Mode

Enabling detailed debugging output.

**Last Updated:** February 8, 2026  
**Audience:** Developers

## Enable Debug Mode

```bash
LOG_LEVEL=DEBUG aurora run
```

Or in config:
```yaml
logging:
  level: DEBUG
  format: detailed
```

## Debug Specific Components

```bash
# Debug specific agent
aurora run --debug-agent backend

# Debug memory
aurora run --debug-memory

# Debug API calls
aurora run --debug-api
```

## Output

Debug mode shows:
- Full API request/response
- Memory queries and results
- Task state transitions
- Token usage per call

## Profiling

```python
import cProfile
await agent.execute(task)
```

## Related Reading

- [Debugging Tips](../06_developer_guides/debugging_tips.md)
