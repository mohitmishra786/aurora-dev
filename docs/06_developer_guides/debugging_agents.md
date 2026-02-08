# Debugging Agents

Psychoanalyzing the machine.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Debugging Failures](../05_user_guides/debugging_failures.md)
> - [Logging Configuration](../13_configuration/logging_configuration.md)

## The Trace

To debug an agent, you need to see its thought process.
Enable tracing in `aurora.yaml`:
```yaml
logging:
  trace_llm: true
```
This logs every prompt/response pair to `.aurora/logs/trace.jsonl`.

## Common Issues

### 1. The Loop of Death
The agent keeps trying the same invalid tool call.
*Cause:* The system prompt didn't clearly explain the tool schema.
*Fix:* Update the tool docstring. The agent reads the docstring to understand how to use the tool.

### 2. Context Overflow
The agent performs poorly on large files.
*Cause:* It ran out of tokens and only saw half the file.
*Fix:* Check `token_usage` in the logs. If close to limit (200k), implement chunking strategies.

### 3. Hallucination
The agent invents a library function.
*Cause:* Temperature too high.
*Fix:* Lower temperature to 0.1 for coding tasks.

## The Debugger Tool

We include a `pdb`-like tool for agents.
```bash
aurora debug --agent backend
```
This pauses execution before every LLM call, allowing you to edit the prompt manually before it is sent.

## Related Reading

- [Debugging Failures](../05_user_guides/debugging_failures.md)
- [Prompt Engineering](../23_research/prompt_engineering.md)
