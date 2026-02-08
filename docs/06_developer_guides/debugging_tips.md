# Debugging Tips

Sherlock Holmes mode.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Debugging Failures](../05_user_guides/debugging_failures.md)
> - [Debugging Agents](./debugging_agents.md)

## The Golden Rule

**Reproduce it locally first.**
Do not try to debug a production issue by reading logs alone. Create a reproduction script.

## Python Debugging

Use `pdb` or `ipdb`.
```python
import ipdb; ipdb.set_trace()
```
This drops you into a shell where you can inspect variables.

## Frontend Debugging

Use **React DevTools**.
- Inspect the Component Tree.
- Check the Props/State.
- Profiler: Find what triggered the re-render.

## Database Debugging

Enable SQL Echo in SQLAlchemy.
```yaml
database:
  echo: true
```
This prints every SQL statement to stdout.

## Network Debugging

Use `curl` or Postman to isolate the API.
```bash
curl -v -X POST http://localhost:8000/api/task -d '{"name": "test"}'
```
Does it work? If yes, the bug is in the UI. If no, the bug is in the API.

## Related Reading

- [Debugging Agents](./debugging_agents.md)
- [Troubleshooting](../14_troubleshooting/getting_help.md)
