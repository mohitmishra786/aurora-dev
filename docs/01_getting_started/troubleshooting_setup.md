# Troubleshooting Setup

Solutions for common issues encountered during AURORA-DEV installation and initial configuration.

**Last Updated:** February 8, 2026  
**Audience:** New Users, Developers

> **Before Reading This**
>
> You should have attempted:
> - [Quickstart](./quickstart.md) or [Installation](./installation.md)
> - Basic troubleshooting like checking Docker status

## Quick Diagnostics

Run the health check first. It identifies most issues:

```bash
python aurora.py health-check --verbose
```

"When debugging, novices insert corrective code; experts remove defective code." Richard Pattis was right. Most setup issues come from misconfiguration, not missing components.

## Docker Issues

### Docker Daemon Not Running

**Symptom:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solution:**

```bash
# Linux
sudo systemctl start docker
sudo systemctl enable docker  # Start on boot

# macOS
open -a Docker  # Or start Docker Desktop from Applications

# Windows
# Start Docker Desktop from the Start Menu
```

### Port Already in Use

**Symptom:**
```
Bind for 0.0.0.0:5432 failed: port is already allocated
```

**Solution:**

Find what's using the port and stop it, or change AURORA-DEV's port:

```bash
# Find the process (Linux/macOS)
lsof -i :5432

# Change port in docker-compose.yml
ports:
  - "5433:5432"  # Use 5433 externally

# Update .env to match
DATABASE_URL=postgresql://aurora:aurora@localhost:5433/aurora
```

```mermaid
flowchart TD
    A[Port Conflict] --> B{Find Process}
    B --> C[Stop Conflicting Service]
    B --> D[Change AURORA Port]
    C --> E[Restart AURORA]
    D --> F[Update .env]
    F --> E
```

### Container Keeps Restarting

**Symptom:**
```
postgres_1  | restarting
postgres_1  | restarting
```

**Solution:**

Check container logs:

```bash
docker-compose logs postgres
```

Common causes:
- Invalid environment variables
- Corrupted data volume
- Insufficient memory

```bash
# Reset data volumes (WARNING: deletes data)
docker-compose down -v
docker-compose up -d
```

## Database Issues

### Connection Refused

**Symptom:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solution:**

1. Verify PostgreSQL is running:
```bash
docker-compose ps postgres
```

2. Check the connection string in `.env`:
```bash
# For Docker Compose (default)
DATABASE_URL=postgresql://aurora:aurora@postgres:5432/aurora

# For local PostgreSQL
DATABASE_URL=postgresql://aurora:aurora@localhost:5432/aurora
```

3. For Docker, use the service name (`postgres`), not `localhost`.

### Authentication Failed

**Symptom:**
```
FATAL: password authentication failed for user "aurora"
```

**Solution:**

The password in `.env` doesn't match what PostgreSQL expects. Reset it:

```bash
# Stop services
docker-compose down -v  # -v removes volumes

# Start fresh
docker-compose up -d
```

## API Key Issues

### Invalid API Key

**Symptom:**
```
anthropic.AuthenticationError: Invalid API key
```

**Solution:**

1. Verify your key format in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

2. No quotes around the value
3. No trailing whitespace
4. Key starts with `sk-ant-`

### Rate Limit Exceeded

**Symptom:**
```
anthropic.RateLimitError: Rate limit exceeded
```

**Solution:**

You've hit Anthropic's rate limits. Options:

1. Wait and retry (automatic with exponential backoff)
2. Reduce parallel agents in configuration:
```bash
# In .env
MAX_PARALLEL_AGENTS=4  # Default is 8
```
3. Upgrade your Anthropic plan for higher limits

## Memory and Performance Issues

### Out of Memory

**Symptom:**
```
Container killed: OOMKilled
```

**Solution:**

Increase Docker memory limits:

```yaml
# docker-compose.yml
services:
  aurora:
    deploy:
      resources:
        limits:
          memory: 4G
```

Or reduce memory usage:

```bash
# In .env
MAX_PARALLEL_AGENTS=2
CACHE_SIZE_MB=256
```

### Slow Performance

**Symptom:** Operations take much longer than expected.

**Solution:**

1. Check Redis is running:
```bash
docker-compose ps redis
```

2. Verify caching is enabled:
```bash
CACHE_ENABLED=true
```

3. Check for network issues to Anthropic API:
```bash
curl -I https://api.anthropic.com/v1/messages
```

## Python Environment Issues

### Module Not Found

**Symptom:**
```
ModuleNotFoundError: No module named 'aurora_dev'
```

**Solution:**

Install dependencies in the correct environment:

```bash
# Activate virtual environment if using one
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep aurora
```

### Python Version Mismatch

**Symptom:**
```
SyntaxError: invalid syntax
```

**Solution:**

AURORA-DEV requires Python 3.11+:

```bash
python --version  # Check version

# Install Python 3.11 if needed
# Ubuntu/Debian
sudo apt install python3.11

# macOS
brew install python@3.11
```

## Getting More Help

If these solutions don't resolve your issue:

1. **Check logs:**
```bash
docker-compose logs --tail=100
```

2. **Enable debug mode:**
```bash
LOG_LEVEL=DEBUG python aurora.py health-check
```

3. **Search existing issues:**
   [github.com/aurora-dev/aurora-dev/issues](https://github.com/aurora-dev/aurora-dev/issues)

4. **Ask the community:**
   [Discord](https://discord.gg/aurora-dev) or [Stack Overflow](https://stackoverflow.com/questions/tagged/aurora-dev)

## Related Reading

- [Installation](./installation.md) - Detailed installation steps
- [System Requirements](./system_requirements.md) - Hardware and software needs
- [Common Errors](../14_troubleshooting/common_errors.md) - Runtime error solutions

## What's Next

- [First Project](./first_project.md) - Build your first application
