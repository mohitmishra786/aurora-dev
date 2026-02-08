# Installation Guide

Complete installation instructions for AURORA-DEV across all supported platforms and deployment scenarios.

**Last Updated:** February 8, 2026  
**Audience:** Developers, Operators

> **Before Reading This**
>
> You should understand:
> - [System Requirements](./system_requirements.md) - Minimum hardware and software
> - Basic Docker and command-line usage

## Installation Methods

AURORA-DEV supports three installation approaches. Choose based on your use case.

| Method | Best For | Complexity |
|--------|----------|------------|
| Docker Compose | Development, small teams | Low |
| Kubernetes | Production, enterprise | Medium |
| Manual | Customization, air-gapped | High |

"Make it work, make it right, make it fast." Kent Beck's advice applies to installation too. Start with Docker Compose. Move to Kubernetes when you need scaling.

## Docker Compose Installation

The recommended approach for most users.

### Prerequisites

```bash
# Verify Docker is installed and running
docker --version    # Requires 24.0+
docker-compose --version  # Requires 2.20+

# Verify Python (for CLI tools)
python --version   # Requires 3.11+
```

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/aurora-dev/aurora-dev.git
cd aurora-dev

# Create environment configuration
cp .env.example .env

# Edit .env with your settings (see Configuration section below)
nano .env  # or your preferred editor

# Install Python dependencies (for CLI)
pip install -r requirements.txt

# Start all services
docker-compose up -d

# Verify installation
docker-compose ps
python aurora.py health-check
```

```mermaid
flowchart LR
    A[Clone Repo] --> B[Configure .env]
    B --> C[Install Dependencies]
    C --> D[Start Services]
    D --> E[Health Check]
    E --> F{All Healthy?}
    F -->|Yes| G[Ready]
    F -->|No| H[Check Logs]
```

### Configuration

The `.env` file controls all configuration. Required settings:

```bash
# Required: Your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Database (defaults work for Docker Compose)
DATABASE_URL=postgresql://aurora:aurora@localhost:5432/aurora

# Redis (defaults work for Docker Compose)
REDIS_URL=redis://localhost:6379
```

Optional settings for production:

```bash
# Security
SECRET_KEY=your-256-bit-secret-key
JWT_SECRET=your-jwt-signing-key

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
PROMETHEUS_ENABLED=true

# Cost controls
DAILY_BUDGET_LIMIT=100.00
MAX_TOKENS_PER_REQUEST=8000
```

See [Environment Variables](../13_configuration/environment_variables.md) for the complete reference.

## Kubernetes Installation

For production deployments requiring horizontal scaling.

### Prerequisites

- Kubernetes cluster (1.28+)
- kubectl configured
- Helm 3.12+
- Persistent volume provisioner

### Installation Steps

```bash
# Add the AURORA-DEV Helm repository
helm repo add aurora-dev https://charts.aurora-dev.io
helm repo update

# Create namespace
kubectl create namespace aurora-dev

# Create secrets
kubectl create secret generic aurora-secrets \
  --namespace aurora-dev \
  --from-literal=anthropic-api-key=sk-ant-your-key \
  --from-literal=database-password=your-db-password \
  --from-literal=redis-password=your-redis-password

# Install with Helm
helm install aurora-dev aurora-dev/aurora-dev \
  --namespace aurora-dev \
  --values values.yaml

# Verify pods are running
kubectl get pods -n aurora-dev
```

See [Kubernetes Deployment](../08_deployment/kubernetes_deployment.md) for detailed configuration.

## Manual Installation

For air-gapped environments or maximum customization.

### Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv postgresql-15 redis-server

# macOS (with Homebrew)
brew install python@3.11 postgresql@15 redis

# Start services
sudo systemctl start postgresql redis  # Linux
brew services start postgresql redis    # macOS
```

### Install AURORA-DEV

```bash
# Clone and setup
git clone https://github.com/aurora-dev/aurora-dev.git
cd aurora-dev

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python manage.py migrate
python manage.py seed_initial_data

# Start the application
python manage.py runserver
```

## Post-Installation Verification

Run the health check to verify all components:

```bash
python aurora.py health-check
```

Expected output:

```
AURORA-DEV Health Check
------------------------
✓ Database connection: healthy
✓ Redis connection: healthy
✓ Anthropic API: healthy (quota: 95% remaining)
✓ Agent registry: 13 agents registered
✓ Memory system: initialized
✓ Task queue: 0 pending, 0 processing

Status: All systems operational
```

## Upgrading

To upgrade an existing installation:

```bash
# Docker Compose
git pull origin main
docker-compose pull
docker-compose up -d

# Kubernetes
helm repo update
helm upgrade aurora-dev aurora-dev/aurora-dev -n aurora-dev
```

See [Upgrade Guide](../08_deployment/upgrade_guide.md) for version-specific migration notes.

## Uninstallation

```bash
# Docker Compose
docker-compose down -v  # -v removes volumes (data loss!)

# Kubernetes
helm uninstall aurora-dev -n aurora-dev
kubectl delete namespace aurora-dev
```

## Related Reading

- [System Requirements](./system_requirements.md) - Hardware and software specifications
- [Docker Deployment](../08_deployment/docker_deployment.md) - Production Docker configuration
- [Environment Variables](../13_configuration/environment_variables.md) - Complete configuration reference

## What's Next

- [First Project](./first_project.md) - Build your first AURORA-DEV application
