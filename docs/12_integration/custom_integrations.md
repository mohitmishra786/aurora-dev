# Custom Integrations

Roll your own.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Creating Plugins](../06_developer_guides/creating_plugins.md)
> - [Webhook Reference](../07_api_reference/websocket_api.md)

## The Integration Interface

Implement the `Integration` abstract base class.

```python
class MyCRMIntegration(Integration):
    def on_task_complete(self, task):
        requests.post("https://my-crm.com/api/update", json={...})
```

## Webhook Outbound

You can configure Generic Webhooks in the UI.
We POST a JSON payload to your URL on specific events.
Signature verification is supported via HMAC-SHA256.

## Plugin approach

Pack your integration as a plugin (`aurora-plugin-mycrm`) and distribute it on PyPI.

## Related Reading

- [Creating Plugins](../06_developer_guides/creating_plugins.md)
- [GitHub Integration](./github_integration.md)
