# Feature Flags

Toggling features without deploying.

**Last Updated:** February 8, 2026
**Audience:** Product Managers

> **Before Reading This**
>
> You should understand:
> - [Environment Variables](./environment_variables.md)
> - [Database Configuration](./database_configuration.md)

## How it works

We use **Unleash** (or a simple DB table) to check flags.

```python
if flags.is_enabled("new_dashboard", user.id):
    return render_new_dashboard()
```

## Config File

For simple setups, `flags.yaml`:
```yaml
new_dashboard:
  enabled: true
  percentage: 50  # 50% rollout
```

## Use Cases

- **Canary Launches:** Enable for 1% of users.
- **Kill Switch:** Disable "Web Search" if the API provider goes down.
- **A/B Testing:** Show blue button to Group A, red to Group B.

## Related Reading

- [Environment Variables](./environment_variables.md)
- [Incident Response](../09_operations/incident_response.md)
