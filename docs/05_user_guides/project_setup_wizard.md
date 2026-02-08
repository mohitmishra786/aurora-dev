# Project Setup Wizard

Interactive guide for creating new AURORA-DEV projects.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Starting the Wizard

```bash
aurora init
```

## Configuration Steps

### Step 1: Project Name
```
? Project name: my-awesome-app
```

### Step 2: Project Type
```
? Project type:
  ❯ Web Application (Full Stack)
    API Only (Backend)
    Frontend Only
    CLI Tool
```

### Step 3: Technology Stack
```
? Backend framework:
  ❯ FastAPI (Python)
    Django (Python)
    Express (Node.js)
    NestJS (Node.js)
```

### Step 4: Database
```
? Database:
  ❯ PostgreSQL
    MySQL
    MongoDB
    None
```

### Step 5: Features
```
? Include features:
  ◉ User Authentication
  ◉ API Documentation
  ◯ Admin Panel
  ◉ Docker Setup
  ◯ Kubernetes Manifests
```

## Generated Structure

```
my-awesome-app/
├── aurora.yaml           # Project configuration
├── requirements.txt
├── docker-compose.yml
├── app/
│   ├── main.py
│   ├── routes/
│   └── models/
└── tests/
```

## Related Reading

- [First Project](../01_getting_started/first_project.md)
- [Environment Variables](../13_configuration/environment_variables.md)
