# Debugging Failures

When the robot gets it wrong.

**Last Updated:** February 8, 2026
**Audience:** All Users

> **Before Reading This**
>
> You should understand:
> - [Troubleshooting Overview](../14_troubleshooting/getting_help.md)
> - [Reflexion Loops](../04_core_concepts/reflexion_loops.md)

## Common Failure Patterns

### 1. The Infinite Loop
The agent tries to fix a bug, fails, reflects, tries the same fix, fails...
*Symptom:* Logs show "Retry 4/5" with identical error messages.
*Fix:* Stop the agent (`Ctrl+C`). Manually edit the file to fix the syntax error that is confusing the parser. Then retry.

### 2. The Context Limit
The agent says "I forgot what file X looks like."
*Symptom:* Hallucinated imports or function names.
*Fix:* Increase `context_window` in `aurora.yaml` or use `aurora memory add <file>` to force it into attention.

### 3. The Tool Error
The agent tries to run `npm install` but `npm` is not in the path.
*Fix:* Ensure your local environment meets the requirements. The agent uses *your* shell.

## Debug Mode

Run with `--debug` to see the raw prompts sent to the LLM.

```bash
aurora run --debug
```

This dumps `prompt.json` and `response.json` to the logs. You can see exactly what context the model saw. Often you will find that the relevant file was missing from context.

## Support

If you are stuck, export the logs:
```bash
aurora logs export
```
And post them to the Discord channel or GitHub Issues.

## Related Reading

- [Common Errors](../14_troubleshooting/common_errors.md)
- [Agent Stuck](../14_troubleshooting/agent_stuck.md)
