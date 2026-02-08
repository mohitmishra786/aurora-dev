# Code Reviewer

The guardian of maintainability.

**Last Updated:** February 8, 2026
**Audience:** Developers, Team Leads

> **Before Reading This**
>
> You should understand:
> - [Coding Standards](../06_developer_guides/coding_standards.md)
> - [Reflexion Loops](../04_core_concepts/reflexion_loops.md)
> - [Base Agent](./00_base_agent.md)

## The Mentor

The Backend Agent writes code that works. The Code Reviewer ensures it is code you *want to keep*.

This agent acts like a Senior Staff Engineer conducting a Pull Request review. It checks for readability, complexity, modularity, and adherence to the project's style guide. It doesn't care if the code compiles (the compiler does that). It cares if the code makes sense to a human 6 months from now.

It flags "Code Smells": massive functions, magic numbers, duplicate logic, and unclear variable names. It suggests refactorings that simplify control flow.

"Any fool can write code that a computer can understand. Good programmers write code that humans can understand." — Martin Fowler. This agent enforces humanity.

## Core Responsibilities

### 1. Style Enforcement
It ensures PEP8 (Python) and Airbnb Style (JS) compliance. But beyond formatting, it checks for idiomatic usage. "Don't use a for-loop here; use a list comprehension."

### 2. Complexity Analysis
It calculates Cyclomatic Complexity. If a function has a score > 10 (too many if/else branches), it requests a refactor.

### 3. Documentation Check
It verifies that every public function has a Docstring explaining *what* it does, *args* it takes, and *returns* it yields. No docstring, no merge.

## Review Flow

```mermaid
graph TD
    PR[Pull Request Created] --> Diff[Analyze Diff]
    
    Diff --> Complexity{Complexity > 10?}
    Complexity -->|Yes| Comment1[Comment: "Function too complex"]
    
    Diff --> Style{Style Violation?}
    Style -->|Yes| Comment2[Comment: "Variable naming unclear"]
    
    Diff --> Logic{Logic Gap?}
    Logic -->|Yes| Comment3[Comment: "Edge case unhandled"]
    
    Comment1 --> RequestChanges[Request Changes]
    Comment2 --> RequestChanges
    Comment3 --> RequestChanges
    
    Complexity -->|No| Clean
    Style -->|No| Clean
    Logic -->|No| Clean
    
    Clean --> Approve[Approve PR]
```

## Tools and Configuration

The agent reads diffs and posts comments.

```yaml
# aurora.yaml
agents:
  code_reviewer:
    model: claude-3-opus-20240229  # Highest nuances for style
    temperature: 0.3
    tools:
      - read_diff
      - post_comment
      - suggest_refactor
    context_window:
      include:
        - "src/**/*.py"
        - "src/**/*.ts"
```

## Best Practices

### "Boy Scout Rule"
"Always leave the campground cleaner than you found it." If the agent sees you touching a file, it might suggest fixing a nearby spelling mistake, even if unrelated to your PR.

### "Explain the Why"
It doesn't just say "Change this." It says "Change this *because* using a Set lookup is O(1) while List lookup is O(n)." It teaches while it corrects.

### "Nitpicks vs Blockers"
It distinguishes between blocking issues (logic bugs) and non-blocking suggestions (variable renaming). It labels comments as `[BLOCKING]` or `[NIT]` to help the developer prioritize.

## Common Failure Modes

### 1. The Pedantic Loop
The agent gets obsessed with a specific style preference that isn't in the official guide.
*Fix:* We align the agent closely with the `coding_standards.md` file. If it's not written down, it's not enforced.

### 2. Context Blindness
Suggesting a refactor that breaks a contract in another file it didn't read.
*Fix:* The `Sematic Search` context allows the reviewer to see usages of the function across the codebase before suggesting changes.

## Related Reading

- [Coding Standards](../06_developer_guides/coding_standards.md)
- [Validator Agent](./13_validator_agent.md)

## What's Next

- [Validator Agent](./13_validator_agent.md)
