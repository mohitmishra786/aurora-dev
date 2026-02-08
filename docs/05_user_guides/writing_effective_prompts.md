# Writing Effective Prompts

How to describe your project for optimal AURORA-DEV results.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## The AURORA Prompt Formula

Good prompts include:
1. **What** - Desired functionality
2. **Who** - Target users
3. **Constraints** - Technology or time limits
4. **Standards** - Quality expectations

## Examples

### ❌ Vague Prompt
```
Build a todo app
```

### ✅ Effective Prompt
```
Build a task management application for small teams (5-10 people).

Features:
- User registration with email verification
- Create, edit, delete tasks with due dates
- Assign tasks to team members
- Filter by status (pending/in-progress/done)
- Email notifications for due tasks

Tech constraints:
- PostgreSQL database
- REST API with FastAPI
- React frontend
- Must handle 100 concurrent users
```

## Prompt Structure

```markdown
# Project: [Name]

## Description
[2-3 sentences describing the application]

## Target Users
[Who will use this and how]

## Core Features
- [Feature 1 with acceptance criteria]
- [Feature 2 with acceptance criteria]

## Non-Functional Requirements
- Performance: [expectations]
- Security: [requirements]
- Scale: [expected load]

## Tech Stack Preferences
[If any]
```

## Related Reading

- [Project Types](./project_types.md)
- [Task Decomposition](../04_core_concepts/task_decomposition.md)
