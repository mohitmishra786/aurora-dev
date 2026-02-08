# Using the Dashboard

Visualizing the brain.

**Last Updated:** February 8, 2026
**Audience:** All Users

> **Before Reading This**
>
> You should understand:
> - [Monitoring Progress](./monitoring_progress.md)
> - [Network Ports](../24_appendices/appendix_d_ports.md)

## Accessing the Dashboard

Start the server:
```bash
aurora server start
```
Navigate to `http://localhost:3000`.

## Features

### 1. The Task Kanban
View tasks in columns: `Pending`, `Planning`, `Executing`, `Review`, `Done`. Drag and drop to reprioritize.

### 2. The Agent Matrix
See which agents are online.
- **Green:** Active
- **Yellow:** Thinking (LLM Request in flight)
- **Red:** Error state

### 3. File Explorer
Browse the logical view of the project. See which files were modified by which agent. "Blame" view shows the Agent ID responsible for every line.

### 4. Memory Inspector
Search the vector database.
Query: "Login"
Result: Shows relevant code snippets and past reflexions. This helps you understand *why* the agent is making certain decisions.

## Security

The dashboard is authenticated. Default credentials are `admin` / `admin`. Please change them immediately in `Settings`.

## Related Reading

- [Monitoring Progress](./monitoring_progress.md)
- [Using CLI](./using_cli.md)
