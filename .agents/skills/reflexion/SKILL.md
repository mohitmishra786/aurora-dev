---
name: reflexion
description: Implement reflexion loops for self-critique, learning from failures, and continuous agent improvement
license: MIT
compatibility: opencode
metadata:
  audience: ai-researchers
  workflow: learning
---

## What I Do

I am the **Reflexion System** - self-improvement mechanism inspired by the Reflexion paper (Shinn et al.). I enable agents to learn from failures.

### Core Responsibilities

1. **Failure Capture**
   - Record task attempts
   - Capture error messages
   - Document approach taken
   - Store test results
   - Track performance metrics

2. **Reflection Generation**
   - Root cause analysis
   - Identify incorrect assumptions
   - Propose alternative approaches
   - Extract generalizable learnings
   - Generate improved strategy

3. **Memory Storage**
   - Link reflections to tasks
   - Store in episodic memory
   - Extract patterns for reuse
   - Update agent knowledge
   - Share learnings across agents

4. **Retry with Knowledge**
   - Apply lessons learned
   - Use improved strategy
   - Add validation steps
   - Monitor progress carefully
   - Measure improvement

## When to Use Me

Use me when:
- An agent fails a task
- Tests don't pass
- Security issues found
- Performance targets not met
- Code review rejected
- Any failure occurs

## Reflexion Pattern

### When Triggered
- Test failures
- Code review rejections
- Security vulnerabilities found
- Performance targets not met
- User acceptance criteria not met

### Process

**1. Capture Failure:**
```yaml
information_gathered:
  - Original task description
  - Agent's approach
  - Code/output produced
  - Test results
  - Error messages
  - Stack traces
  - Performance metrics
```

**2. Generate Reflection:**

**LLM Prompt:**
```
You attempted to complete this task:
{task_description}

Your approach was:
{approach_taken}

The code you wrote:
{code}

Test results:
{test_results}

Errors encountered:
{errors}

Performance metrics:
{metrics}

This was attempt #{attempt_number}.

Provide a detailed reflection:

1. ROOT CAUSE ANALYSIS
- What exactly went wrong?
- Why did it happen?
- What was fundamental error in reasoning?

2. INCORRECT ASSUMPTIONS
- What did you assume that was wrong?
- What did you overlook?
- What edge cases did you miss?

3. ALTERNATIVE APPROACHES
- What should you try differently?
- What patterns or techniques would work better?
- What additional validation is needed?

4. GENERALIZABLE LEARNINGS
- What lesson applies to similar tasks?
- What pattern should you remember?
- What should you check for next time?

Be specific and actionable. Focus on what to change, not just what went wrong.
```

**Output Structure:**
```yaml
root_cause:
  technical: str
  reasoning: str

incorrect_assumptions:
  - assumption: str
    why_wrong: str
    correct_approach: str

improved_strategy:
  approach: str
  implementation_steps: [str]
  validation_plan: str

lessons_learned:
  - lesson: str
    applicability: str
    pattern_name: str
```

**3. Store Reflection:**

**Episodic Memory:**
- Link to original task
- Full reflection
- Attempt number
- Timestamp
- Agent ID

**Pattern Library:**
- If generalizable, extract pattern
- Add to shared knowledge
- Make available to all agents

**4. Retry with Knowledge:**

**Enhanced Context:**
- Original task
- Previous attempts summary
- Reflections from all attempts
- Relevant pattern from memory
- Similar successful tasks

**Retry with Improvements:**
- Apply lessons learned
- Use improved strategy
- Add suggested validation
- Monitor progress more carefully

## Example Reflexion

**Task:** Implement user authentication

**Attempt 1:**
- Approach: Store passwords in plain text
- Error: Security audit flagged critical vulnerability

**Reflexion:**
```yaml
root_cause:
  technical: Passwords stored without hashing
  reasoning: Didn't consider security best practices

incorrect_assumptions:
  - "Simple storage is acceptable" → Wrong
  - "Application-level security sufficient" → Wrong

improved_strategy:
  approach: Use bcrypt for password hashing
  implementation:
    - Hash password before storing
    - Use high cost factor (12+)
    - Add salt automatically
    - Never retrieve or log passwords
  validation:
    - Security audit
    - Penetration testing
    - Check against OWASP guidelines

lessons_learned:
  - Always hash passwords (bcrypt, Argon2)
  - Never store sensitive data in plain text
  - Security audit before deployment
  - Follow OWASP authentication guidelines
```

**Attempt 2:**
- Approach: bcrypt hashing with cost factor 12
- Result: All tests pass, security audit clean
- Status: SUCCESS

**Pattern Stored:**
```yaml
name: secure_password_storage
description: Hash passwords with bcrypt
implementation: |
  import bcrypt
  
  def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()
  
  def verify_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash.encode())
applies_to:
  - User authentication
  - Password reset
  - Any credential storage
```

## Best Practices

When working with me:
1. **Accept failures** - They're learning opportunities
2. **Be specific** - Vague reflections aren't actionable
3. **Extract patterns** - Generalize learnings for reuse
4. **Document everything** - Future agents will benefit
5. **Measure improvement** - Track reflexion effectiveness

## What I Learn

I store in memory:
- Root cause patterns
- Common mistakes
- Effective solutions
- Best practices
- Anti-patterns to avoid

This enables continuous improvement across all agents.
