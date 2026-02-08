# Tutorial 05: Deployment

Going live with Docker.

**Last Updated:** February 8, 2026
**Difficulty:** Intermediate
**Time:** 15 mins

## Goal

Containerize the app and run it with Docker Compose.

## Step 1: Task Definition

```markdown
# Objective
Create a `Dockerfile` for the FastAPI backend.
Create a `Dockerfile` for the React frontend.
Create a `docker-compose.yaml` to run both services.
Map backend to port 8000 and frontend to 3000.
```

## Step 2: Run Agent

```bash
aurora run --task task.md --agent devops
```

## Step 3: Build & Run

```bash
docker-compose up --build
```

## Next Step

[Tutorial 06: Monitoring](./tutorial_06_monitoring.md)
