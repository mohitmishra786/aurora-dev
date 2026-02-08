# Deployment Failures

It works on my machine...

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [Docker Deployment](../08_deployment/docker_deployment.md)
> - [Kubernetes Deployment](../08_deployment/kubernetes_deployment.md)

## ImagePullBackOff

*Cause:* Registry credentials missing or image tag wrong.
*Fix:* `kubectl create secret docker-registry`. Verify image exists.

## CrashLoopBackOff

*Cause:* App crashing immediately configuration error.
*Fix:* `kubectl logs pod-name`. Look for "Env Var missing".

## Pending

*Cause:* Insufficient CPU/RAM in cluster.
*Fix:* Add nodes or reduce requests.

## Related Reading

- [Kubernetes Deployment](../08_deployment/kubernetes_deployment.md)
- [Environment Variables](../13_configuration/environment_variables.md)
