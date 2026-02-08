# Deploying to GCP

Google's playground.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Kubernetes Deployment](./kubernetes_deployment.md)
> - [Infrastructure Diagram](../21_diagrams/architecture/infrastructure_diagram.mmd)

## Components

- **Compute:** GKE (Google Kubernetes Engine) - Autopilot recommended.
- **Database:** Cloud SQL for PostgreSQL.
- **Cache:** Memorystore for Redis.
- **AI:** Vertex AI (for Gemini integration).

## GKE Autopilot

Simply run:
```bash
gcloud container clusters create-auto aurora \
    --region us-central1 \
    --project my-project
```

## Vertex AI Integration

If using Gemini models, you don't need API keys. Just grant the `Vertex AI User` role to the K8s Service Account via Workload Identity.

## Cloud Build

We include `cloudbuild.yaml` for CI/CD.
Triggers on push to `main` -> Builds Docker image -> Deploys to GKE.

## Related Reading

- [Cloud AWS](./cloud_aws.md)
- [Disaster Recovery](./disaster_recovery.md)
