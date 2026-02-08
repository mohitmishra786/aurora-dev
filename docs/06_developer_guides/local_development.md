# Local Development Setup

Running AURORA-DEV for development purposes.

**Last Updated:** February 8, 2026  
**Audience:** Developers

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

## Quick Setup

```bash
# Clone repository
git clone https://github.com/aurora-dev/aurora-dev.git
cd aurora-dev

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Start services
docker-compose -f docker-compose.dev.yml up -d

# Run database migrations
alembic upgrade head

# Start development server
uvicorn aurora_dev.main:app --reload
```

## Development Configuration

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://aurora:aurora@localhost:5432/aurora_dev
REDIS_URL=redis://localhost:6379
LOG_LEVEL=DEBUG
```

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=aurora_dev --cov-report=html

# Specific test
pytest tests/unit/test_maestro.py -v
```

## Related Reading

- [Installation](../01_getting_started/installation.md)
- [Coding Standards](./coding_standards.md)
