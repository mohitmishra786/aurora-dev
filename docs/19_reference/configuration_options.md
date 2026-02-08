# Configuration Options

Every knob and dial.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Environment Variables](../13_configuration/environment_variables.md)
> - [Agent Configuration](../13_configuration/agent_configuration.md)

## `aurora.yaml`

The master config file.

### `server`
```yaml
server:
  host: 0.0.0.0
  port: 8080
  workers: 4
  timeout: 60
```

### `database`
```yaml
database:
  pool_size: 20
  echo: false
```

### `memory`
```yaml
memory:
  backend: qdrant
  collection: aurora
```

### `logging`
```yaml
logging:
  level: INFO
  format: json
  file: /var/log/aurora.log
```

## Related Reading

- [Environment Variables](../13_configuration/environment_variables.md)
- [Agent Configuration](../13_configuration/agent_configuration.md)
