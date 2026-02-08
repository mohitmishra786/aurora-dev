# Agent Configuration

Tuning the brains.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Environment Variables](./environment_variables.md)
> - [Agent Specifications](../03_agent_specifications/00_base_agent.md)

## `agents.yaml`

We support defining agent behavior in a YAML file.

```yaml
agents:
  backend:
    model: "claude-3-opus"
    temperature: 0.1
    timeout: 300
    system_prompt_override: "You are a senior backend engineer..."
    tools:
      - "read_file"
      - "run_shell"
  
  frontend:
    model: "gpt-4-turbo"
    temperature: 0.2
    tools:
      - "read_file"
      - "generate_image"
```

## Runtime Overrides

You can pass configuration per-task via the API.
This is useful for trying out a higher temperature for creative tasks.

## Tool Permissions

You can whitelist/blacklist tools per agent.
```yaml
    blacklist:
      - "delete_file"
```

## Related Reading

- [Model Selection](./model_selection.md)
- [Customizing Agents](../05_user_guides/customizing_agents.md)
