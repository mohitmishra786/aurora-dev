# Project Types

AURORA-DEV templates for different application types.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Available Templates

### Web Application (Full Stack)
```bash
aurora init --template fullstack
```
Generates: FastAPI backend, React frontend, PostgreSQL, Docker

### API Only
```bash
aurora init --template api
```
Generates: FastAPI, PostgreSQL, OpenAPI docs, Docker

### Frontend Only
```bash
aurora init --template frontend
```
Generates: React/Vue/Next.js, component library, build tooling

### CLI Tool
```bash
aurora init --template cli
```
Generates: Click/Typer CLI, tests, distribution config

### Microservices
```bash
aurora init --template microservices
```
Generates: Multiple services, API gateway, K8s manifests

## Template Comparison

| Feature | Fullstack | API | Frontend | CLI |
|---------|-----------|-----|----------|-----|
| Backend | ✓ | ✓ | - | ✓ |
| Frontend | ✓ | - | ✓ | - |
| Database | ✓ | ✓ | - | Optional |
| Docker | ✓ | ✓ | ✓ | Optional |
| K8s | Optional | Optional | - | - |

## Custom Templates

Create your own:
```yaml
# templates/my-template.yaml
name: my-custom-template
extends: fullstack
overrides:
  backend_framework: django
  database: mysql
```

## Related Reading

- [Project Setup Wizard](./project_setup_wizard.md)
- [First Project](../01_getting_started/first_project.md)
