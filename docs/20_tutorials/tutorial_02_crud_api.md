# Tutorial 02: CRUD API

Building a To-Do list backend.

**Last Updated:** February 8, 2026
**Difficulty:** Beginner
**Time:** 15 mins

## Goal

Build a FastAPI app with endpoints to Create, Read, Update, and Delete tasks.

## Step 1: Task Definition

Create `task.md`:
```markdown
# Objective
Create a FastAPI application in `main.py`.
It should have a `Task` model (id, title, done).
Implement GET /tasks, POST /tasks, PUT /tasks/{id}, DELETE /tasks/{id}.
Use an in-memory list for storage.
```

## Step 2: Run Agent

```bash
aurora run --task task.md --agent backend
```

## Step 3: Test

```bash
uvicorn main:app --reload
curl -X POST http://localhost:8000/tasks -d '{"title": "Buy milk"}'
```

## Next Step

[Tutorial 03: Fullstack App](./tutorial_03_fullstack_app.md)
