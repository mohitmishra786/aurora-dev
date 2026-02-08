# Runbook Templates

Standard operating procedures for AURORA-DEV.

**Last Updated:** February 8, 2026  
**Audience:** DevOps Engineers

## Agent Stuck

**Symptoms:** Task not progressing for > 30 minutes

**Steps:**
1. Check logs: `aurora logs -a <agent> -t <task>`
2. Check resource usage: `kubectl top pods`
3. Retry task: `aurora task retry <task-id>`
4. If persistent, restart agent: `aurora agent restart <agent>`

## High Error Rate

**Symptoms:** Error rate > 5%

**Steps:**
1. Check error logs: `aurora logs -l error`
2. Identify pattern (API, DB, external)
3. Check external service status
4. Scale if load-related

## Budget Alert

**Symptoms:** Daily budget > 80%

**Steps:**
1. Review usage: `aurora costs --daily`
2. Pause non-critical projects
3. Switch to cheaper models if possible
4. Alert stakeholders

## Template

```markdown
## [Issue Name]

**Symptoms:** [How to identify]

**Impact:** [What's affected]

**Steps:**
1. [Diagnostic step]
2. [Resolution step]
3. [Verification step]

**Escalation:** [When to escalate]
```
