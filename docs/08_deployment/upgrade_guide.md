# Upgrade Guide

Moving up the version ladder.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Changelog](../19_reference/changelog.md)
> - [Docker Deployment](./docker_deployment.md)

## SemVer Policy

We follow Semantic Versioning.
- **Micro (1.0.1):** Safe to auto-update.
- **Minor (1.1.0):** Check release notes for new features.
- **Major (2.0.0):** Breaking changes. Manual intervention required.

## The Process

1. **Read Release Notes:** Check `CHANGELOG.md` for breaking changes.
2. **Back up DB:** Always.
3. **Pull Image:** `docker pull aurora/core:new-tag`.
4. **Run Migrations:** `aurora db upgrade`.
5. **Restart Containers:** `docker-compose restart`.

## Rolling Updates (K8s)

Kubernetes handles this automatically.
If a new pod fails the Health Check, the rollout pauses, and old pods serve traffic.

## Downgrading

If things go wrong:
1. `aurora db downgrade base` (Careful! This might lose data).
2. Revert Docker image tag.

## Related Reading

- [Changelog](../19_reference/changelog.md)
- [Backup & Restore](./backup_restore.md)
