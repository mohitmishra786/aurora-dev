# Best Practices

The path to enlightenment.

**Last Updated:** February 8, 2026
**Audience:** All Users

> **Before Reading This**
>
> You should understand:
> - [Coding Standards](../06_developer_guides/coding_standards.md)
> - [Agent Configuration](../13_configuration/agent_configuration.md)

## Prompt Engineering

Garbage In, Garbage Out. To get good code, you must ask good questions.

### 1. Be Specific
- **Bad:** "Make the login page look better."
- **Good:** "Update the login page to use Tailwind CSS. Center the form card. Use a gradient background (blue-500 to purple-600)."

### 2. Provide Context
If you want the agent to use a specific library, tell it. "Use `zod` for validation." If you don't, it might use `yup` or `joi`.

## Workflow Optimization

### 1. Review Early
Don't wait for the agent to write 50 files. Review the `plan.md` first. If the plan is wrong, the code will be wrong.

### 2. Run Tests Frequently
Use `aurora test --watch`. Catch regressions instantly.

## Cost Management

### 1. Use Haiku for Simple Tasks
Set `model: claude-3-haiku` for tasks like "Add comments" or "Fix typos." It's 50x cheaper than Opus.

### 2. Limit Context
Don't include the entire `node_modules` folder in context. Use `.auroraignore` to exclude noise.

## Security

### 1. Never Commit Secrets
The `Security Agent` will yell at you, but it's better if you don't do it in the first place. Use `.env` files.

### 2. Review Dependencies
Agents love to add npm packages. Verify that `left-pad` is actually needed before merging.

## Related Reading

- [Writing Effective Prompts](./writing_effective_prompts.md)
- [Managing Costs](./managing_costs.md)
