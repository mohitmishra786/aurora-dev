# Iterative Development

Making changes to existing AURORA-DEV projects.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Adding Features

```bash
aurora add feature "Add password reset functionality"
```

AURORA-DEV will:
1. Analyze existing codebase
2. Plan minimal changes
3. Implement without breaking existing code
4. Update tests

## Modifying Existing Code

```bash
aurora modify "Change task priorities to use enum instead of int"
```

## Bug Fixes

```bash
aurora fix "Login fails when email has uppercase letters"
```

The fix workflow:
1. Reproduce the issue
2. Identify root cause
3. Implement fix
4. Add regression test

## Refactoring

```bash
aurora refactor "Move database queries to repository pattern"
```

Safe refactoring:
- Runs all tests before changes
- Makes incremental changes
- Runs tests after each step
- Rolls back on failure

## Version Control

Each change creates:
- Feature branch
- Atomic commits
- Pull request (optional)

```bash
# View changes before accepting
aurora diff

# Accept changes
aurora apply
```

## Related Reading

- [Reflexion Loops](../04_core_concepts/reflexion_loops.md)
- [Quality Gates](../04_core_concepts/quality_gates.md)
