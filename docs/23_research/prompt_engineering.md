# Prompt Engineering Architecture

The source code of the mind.

**Last Updated:** February 8, 2026
**Audience:** Prompt Engineers, AI Developers

> **Before Reading This**
>
> You should understand:
> - [Agent Configuration](../13_configuration/agent_configuration.md)
> - [Context Management](../04_core_concepts/context_management.md)

## Prompts as Software

In AURORA-DEV, we treat prompts like code. They are versioned, modular, and tested. We do not use "magic strings" scattered throughout the codebase. We use a structured Prompt Library (`aurora_dev.core.prompts`).

A system prompt is not just a sentence. It is a compiled artifact containing:
1. **Identity & Role**: "You are a Senior Python Engineer."
2. **Context Instantiation**: "You are working on Project X."
3. **Tool Definitions**: "You have access to `grep`, `sed`."
4. **Constraint Injection**: "Do not use `time.sleep()`."
5. **Output Schema**: "Reply in valid JSON."

## The CO-STAR Framework

We adhere to the CO-STAR framework for all system prompts:

- **C**ontext: Background information (Project type, current phase).
- **O**bjective: The specific task (Write a function, debug an error).
- **S**tyle: The tone (Professional, terse, technical).
- **T**one: The attitude (Helpful but strict).
- **A**udience: Who reads the output (Parser? Human? Another agent?).
- **R**esponse: The format (JSON, Markdown, Diff).

## Dynamic Prompt Construction

We don't send static text to Claude. We build prompts at runtime.

```python
def build_system_prompt(agent, project, task):
    base = load_prompt("roles", agent.role)
    constraints = load_prompt("constraints", project.compliance_level)
    memory = memory_store.get_relevant_patterns(task)
    
    return f"""
    {base}
    
    CURRENT PROJECT: {project.name}
    
    RELEVANT MEMORIES:
    {memory}
    
    HARD CONSTRAINTS:
    {constraints}
    """
```

This "Prompt Injection" (the good kind) ensures the agent is context-aware without being context-flooded.

## Chain of Thought (CoT)

We force **Chain of Thought** in every complex task. We ask the agent to `<thinking>` before `<answering>`.

Why? Because LLMs compute linearly. They cannot "change their mind" about the start of a sentence once they have written it. By forcing them to output a thinking block first, we give them "scratchpad" space to perform intermediate reasoning steps before committing to a solution.

For example, asking "Is this number prime?" might result in a hallucination. Asking "Divide this number by 2, 3, 5... Is it prime?" results in the correct answer.

## Meta-Prompting

We use agents to write prompts for other agents. The `Architect Agent` generates the task description for the `Backend Agent`.

*Architect Output:*
> "Create a `User` model. It must have an `email` field."

*Backend System Prompt:*
> "You are the Backend Agent. The Architect has instructed: 'Create a User model...'"

This daisy-chaining requires high fidelity. If the Architect is vague, the Backend will be confused. We tune the Architect's prompt to be "Descriptive and precise, like a RFC spec."

## Optimization

We continuously optimize prompts based on the **Reflexion** data. If we see agents frequently forgetting to add docstrings, we patch the global `coding_standards` prompt chunk to shout "ADD DOCSTRINGS" more loudly.

## Related Reading

- [Context Optimization](./context_optimization.md)
- [Coding Standards](../06_developer_guides/coding_standards.md)

## What's Next

- [Context Optimization](./context_optimization.md)
