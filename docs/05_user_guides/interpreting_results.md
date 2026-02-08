# Interpreting Results

Understanding what the machine built.

**Last Updated:** February 8, 2026
**Audience:** All Users

> **Before Reading This**
>
> You should understand:
> - [Understanding Agent Output](./understanding_agent_output.md)
> - [Reviewing Generated Code](./reviewing_generated_code.md)

## The "Done" Signal

When `aurora run` completes, it prints a Summary Report.
```text
Task Completed: Build Login System
- 5 new files created (src/auth/...)
- 3 tests passed
- Security Scan: Clean
- Cost: $0.45
```

## Verifying Quality

Don't just trust the green checkmark.
1. **Run the App:** `docker-compose up`. Does it boot?
2. **Click the Buttons:** Go to `/login`. Can you actually log in?
3. **Read the Code:** Is it readable? Does it follow your style guide?

## Handling Halucinations

Sometimes the agent lies. "I fixed the bug," it says, but the bug remains.
- **Check the Tests:** Did it write a *new* test that passes, or did it just skip the failing test?
- **Check the Logs:** Did it encounter an error and "Reflect" that it was irrelevant?

## The Artifacts Folder

Output files are stored in `.aurora/artifacts/`.
- `plan.md`: The strategy document.
- `diagram.png`: The architecture visualization.
- `audit.json`: The security report.

Review these to understand the *decision process* behind the code.

## Related Reading

- [Reviewing Generated Code](./reviewing_generated_code.md)
- [Debugging Failures](./debugging_failures.md)
