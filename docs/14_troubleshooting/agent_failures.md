# Agent Failures

When the AI gives up.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Debugging Agents](../06_developer_guides/debugging_agents.md)
> - [Common Errors](./common_errors.md)

## The "I can't do that" Response

If the agent refuses to edit a file.
*Reason:* Guardrails. The system prompt prevents destructive actions.
*Fix:* Check `SafeToAutoRun` permissions or explicit user approval settings.

## Parsing Errors

"Could not parse tool call."
*Reason:* The LLM output bad JSON.
*Fix:* The system automatically retries 3 times with the error message. If it persists, switch to a smarter model (Opus).

## Hallucinations

The agent imports a made-up library.
*Reason:* It saw it in training data but it doesn't exist in your repo.
*Fix:* Add a `dependency_check` step in the plan.

## Related Reading

- [Debugging Agents](../06_developer_guides/debugging_agents.md)
- [Model Selection](../13_configuration/model_selection.md)
