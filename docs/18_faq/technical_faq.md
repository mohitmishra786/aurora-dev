# Technical FAQ

Technical questions about AURORA-DEV.

**Last Updated:** February 8, 2026  
**Audience:** Developers

## Architecture

### Why LangGraph?
Provides robust state machine with checkpointing and parallel execution support.

### Why three memory tiers?
Balances speed (Redis), persistence (PostgreSQL), and intelligence (Mem0).

### Can agents run in parallel?
Yes, using Git worktrees for isolation.

## Integration

### Does it work with my IDE?
Yes, generates standard projects compatible with any IDE.

### Can I integrate with existing CI/CD?
Yes, generates GitHub Actions/GitLab CI configs.

### Does it support custom frameworks?
Core frameworks are supported. Custom frameworks via configuration.

## Performance

### How many agents can run in parallel?
Default 4, configurable up to 10.

### What's the token limit?
Uses up to 200k context tokens per agent call.

## Related Reading

- [Architecture Overview](../02_architecture/system_overview.md)
