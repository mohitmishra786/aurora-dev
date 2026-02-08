# Creating Projects

Starting from scratch (or a template).

**Last Updated:** February 8, 2026
**Audience:** All Users

> **Before Reading This**
>
> You should understand:
> - [Project Setup Wizard](./project_setup_wizard.md)
> - [Project Types](./project_types.md)

## The Blank Canvas

Creating a project in AURORA-DEV is more than just making a folder. It initializes the "Brain"—the memory store, the agent configuration, and the Docker environment.

## The CLI Wizard

The easiest way to start is the interactive wizard.

```bash
$ aurora init
```

The `Maestro Agent` will interview you:

> **Maestro:** "Hello! What are we building today?"
> **You:** "A social network for cats."
> **Maestro:** "Exciting. Should this be a web app (React/Python) or mobile (React Native)?"
> **You:** "Web app."

Based on this conversation, the agent generates the `aurora.yaml` configuration.

## Manual Creation

You can also skip the chat and pass flags.
```bash
aurora init --type fullstack --name catbook
```
This scaffolds a standard Next.js + FastAPI + Postgres stack.

## File Structure

After initialization, you will see key files:

- `aurora.yaml`: Variable definitions.
- `.aurora/`: The brain folder. *Do not delete.*
- `task.md`: The roadmap.
- `docker-compose.yml`: The local infrastructure.

## Next Steps

1. **Review the Plan:** Open `task.md`. The Architect Agent has already filled it with a proposed roadmap.
2. **Start the Engine:** Run `aurora run`.
3. **Grab Coffee:** Watch the agents clone repos, install dependencies, and write the Hello World code.

## Related Reading

- [Project Setup Wizard](./project_setup_wizard.md)
- [Using CLI](./using_cli.md)
