# Customizing Agents

Teaching old bots new tricks.

**Last Updated:** February 8, 2026
**Audience:** Power Users, Developers

> **Before Reading This**
>
> You should understand:
> - [Agent Configuration](../13_configuration/agent_configuration.md)
> - [Prompt Engineering](../23_research/prompt_engineering.md)

## Modifying Roles

The default `Backend Agent` is a Python expert. But what if you are a Go shop?
You can override the system prompt in `aurora.yaml`:

```yaml
agents:
  backend:
    system_prompt: |
      You are a Senior Go Engineer.
      You prefer standard library over frameworks.
      Always use `gofmt`.
```

This simple change fundamentally alters the code it produces.

## Adding Tools

You can give agents new capabilities.
If you have a customized internal CLI tool (`corp-cli`), register it:

```yaml
agents:
  devops:
    tools:
      - name: run_corp_cli
        description: "Deploys to corporate cloud"
        command: "corp-cli deploy {args}"
```

Now the DevOps agent can deploy to your private cloud.

## Limiting Power

Sometimes agents are too powerful. You can restrict them.
```yaml
agents:
  junior_dev:
    permissions:
      filesystem: ["read_only"]
      network: ["none"]
```
This is useful for agents that just do analysis or documentation.

## Related Reading

- [Agent Configuration](../13_configuration/agent_configuration.md)
- [Custom Agent Development](../17_advanced_topics/custom_agent_development.md)
