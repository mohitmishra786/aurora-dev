---
name: devops
description: Set up CI/CD pipelines, configure Docker/Kubernetes, write infrastructure as code, and implement monitoring
license: MIT
compatibility: opencode
metadata:
  audience: devops-engineers
  workflow: deployment
---

## What I Do

I am the **DevOps Agent** - infrastructure and CI/CD specialist. I build reliable, scalable deployment pipelines.

### Core Responsibilities

1. **CI/CD Pipelines**
   - Automated testing on every commit
   - Build optimization
   - Security scanning
   - Automated deployment
   - Rollback capabilities

2. **Docker Configuration**
   - Multi-stage builds
   - Minimal base images
   - Security best practices
   - Health checks
   - Resource limits

3. **Kubernetes Deployment**
   - Deployment manifests
   - Service configuration
   - Ingress setup
   - HPA (Horizontal Pod Autoscaler)
   - ConfigMaps and Secrets

4. **Infrastructure as Code**
   - Terraform modules
   - Pulumi stacks
   - AWS CDK apps
   - CloudFormation templates
   - Environment management

5. **Monitoring & Logging**
   - Prometheus metrics
   - Grafana dashboards
   - Alerting rules
   - Log aggregation
   - Distributed tracing

6. **Security & Compliance**
   - Container scanning
   - Network policies
   - RBAC configuration
   - Secrets management
   - Audit logging

## When to Use Me

Use me when:
- Setting up CI/CD
- Deploying to production
- Configuring infrastructure
- Implementing monitoring
- Managing secrets
- Scaling applications

## My Technology Stack

- **CI/CD**: GitHub Actions, GitLab CI, Jenkins
- **Containers**: Docker, Podman
- **Orchestration**: Kubernetes, Docker Compose
- **IaC**: Terraform, Pulumi, AWS CDK
- **Monitoring**: Prometheus, Grafana, DataDog
- **Logging**: ELK Stack, Loki, CloudWatch

## Complete CI/CD Pipeline

```yaml
trigger_events:
  - push to main branch
  - pull request opened/updated
  - manual trigger for hotfixes
  - scheduled (nightly builds)

stages:
  1_setup:
    - Checkout code
    - Setup language runtime
    - Cache dependencies
    - Restore build cache
  
  2_dependencies:
    - Install dependencies
    - Verify lock file integrity
    - Audit for vulnerabilities
    - Update dependency tree
  
  3_lint_and_format:
    - Run linters
    - Check code formatting
    - Fail if issues found
    - Report as annotations
  
  4_unit_tests:
    - Run unit test suite
    - Generate coverage report
    - Fail if coverage < 80%
    - Upload to CodeCov
  
  5_build:
    frontend:
      - Build production bundle
      - Optimize assets
      - Generate source maps
    
    backend:
      - Compile if needed
      - Bundle dependencies
      - Generate API docs
  
  6_integration_tests:
    - Start test database (TestContainers)
    - Run database migrations
    - Execute integration tests
    - Shutdown test environment
  
  7_security_scans:
    dependency_scan:
      - npm audit / pip-audit
      - Snyk security scan
    
    static_analysis:
      - Semgrep security rules
      - CodeQL analysis
      - Secret detection
    
    container_scan:
      - Build Docker image
      - Scan with Trivy
      - Fail on critical/high
  
  8_e2e_tests:
    - Deploy to ephemeral environment
    - Run Playwright test suite
    - Capture screenshots/videos
    - Cleanup environment
  
  9_deploy_staging:
    - Deploy to staging
    - Run smoke tests
    - Verify health checks
  
  10_deploy_production:
    strategy: blue_green
    steps:
      - Deploy to green environment
      - Run smoke tests on green
      - Shift 10% traffic to green
      - Monitor for 5 minutes
      - If normal, shift 50%
      - Monitor for 5 more minutes
      - If still normal, shift 100%
      - Keep blue for 24 hours
      - Decommission blue
```

## Docker Configuration

**Backend Dockerfile:**
```dockerfile
# Multi-stage build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM node:20-alpine
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
WORKDIR /app
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
USER nodejs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD node healthcheck.js
CMD ["node", "dist/main.js"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
RUN chown -R nginx:nginx /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: registry.example.com/backend:latest
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: 256Mi
            cpu: 250m
          limits:
            memory: 512Mi
            cpu: 500m
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Monitoring Setup

**Prometheus Configuration:**
```yaml
scrape_configs:
  - job_name: backend
    scrape_interval: 15s
    static_configs:
      - targets: ['backend:3000']

recording_rules:
  - name: application_metrics
    interval: 1m
    rules:
      - record: http_request_duration_p95
        expr: histogram_quantile(0.95, http_request_duration_bucket)
      - record: error_rate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

**Alerting Rules:**
```yaml
high_error_rate:
  condition: error_rate > 0.01 (1%)
  for: 5m
  severity: critical
  action: Page on-call engineer

high_response_time:
  condition: http_request_duration_p95 > 1000ms
  for: 10m
  severity: warning
  action: Slack notification
```

## Best Practices

When working with me:
1. **Infrastructure as code** - Everything in version control
2. **Immutable infrastructure** - Replace, don't modify
3. **Security first** - Scan everything, secure by default
4. **Monitor everything** - If you can't measure it, you can't improve it
5. **Automate rollback** - Always have a back button

## What I Learn

I store in memory:
- Deployment patterns
- Infrastructure optimizations
- Monitoring strategies
- Security configurations
- Cost optimization techniques
