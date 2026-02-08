# Using the CLI

Commanding the machine from the terminal.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Installation](../01_getting_started/installation.md)
> - [Command Reference](../24_appendices/appendix_a_commands.md)

## The `aurora` Command

The CLI is your primary interface. It is built with `Typer` and supports rich text output.

```bash
aurora [OPTIONS] COMMAND [ARGS]...
```

## Common Workflows

### 1. Starting a New Feature
```bash
aurora task add "Create a user profile page with avatar upload"
aurora run
```

### 2. Checking Status
```bash
aurora status
> Current Task: Implementing Profile Page
> Agent: Frontend Agent
> Step: 3/5 (Writing Component)
```

### 3. Interactive Mode
```bash
aurora chat
> You: How do I reset the database?
> Aurora: Run `aurora db reset`.
```

## Advanced Flags

- `--verbose`: Show detailed logs, including LLM prompts.
- `--dry-run`: Plan the work but do not write files.
- `--model <name>`: Override the default model for this session.

## Configuration

The CLI reads from `aurora.yaml` in the current directory. You can override this:
```bash
aurora --config /path/to/other.yaml run
```

## Related Reading

- [Command Reference](../24_appendices/appendix_a_commands.md)
- [Keyboard Shortcuts](../24_appendices/appendix_b_shortcuts.md)
