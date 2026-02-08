# CI/CD Pipelines

Continuous integration and deployment for AURORA-DEV.

**Last Updated:** February 8, 2026  
**Audience:** DevOps Engineers

## GitHub Actions

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest --cov

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t aurora .
      - run: docker push ghcr.io/aurora-dev/aurora-dev:latest
```

## GitLab CI

```yaml
stages:
  - test
  - deploy

test:
  stage: test
  image: python:3.11
  script:
    - pip install -e ".[dev]"
    - pytest --cov

deploy:
  stage: deploy
  image: docker:latest
  script:
    - docker build -t aurora .
    - docker push registry.gitlab.com/aurora/aurora-dev:latest
```

## Related Reading

- [Docker Deployment](./docker_deployment.md)
