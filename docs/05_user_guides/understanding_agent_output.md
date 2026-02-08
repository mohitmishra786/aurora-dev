# Understanding Agent Output

Interpreting AURORA-DEV's generated artifacts.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Output Types

| Type | Location | Description |
|------|----------|-------------|
| Source Code | `project/` | Generated application code |
| Tests | `project/tests/` | Automated test suites |
| Docs | `project/docs/` | API and user documentation |
| Configs | `project/` | Docker, K8s, CI/CD files |
| Logs | `.aurora/logs/` | Agent execution logs |

## Reading Agent Logs

```
[2024-02-08T10:30:15Z] [MAESTRO] Starting task decomposition
[2024-02-08T10:30:18Z] [MAESTRO] Created 12 tasks
[2024-02-08T10:30:20Z] [BACKEND] Assigned task: Create user model
[2024-02-08T10:31:45Z] [BACKEND] Task completed (85 seconds)
```

## Progress Dashboard

```
╔══════════════════════════════════════════════════════╗
║ Project: my-app                                      ║
║ Status: IMPLEMENTING (65% complete)                  ║
╠══════════════════════════════════════════════════════╣
║ ✓ Planning          │ ◉ Implementation │ ○ Testing  ║
║ ✓ Architecture      │ ◉ Backend (3/5)  │ ○ Review   ║
║                     │ ◉ Frontend (2/4) │            ║
╠══════════════════════════════════════════════════════╣
║ Active Agents: 3    │ Cost: $4.50      │ ETA: 15min ║
╚══════════════════════════════════════════════════════╝
```

## Quality Reports

After completion, review:
- `reports/test_coverage.html` - Test coverage
- `reports/security_scan.json` - Security findings
- `reports/code_review.md` - Review summary

## Related Reading

- [Progress Monitoring](./progress_monitoring.md)
- [Troubleshooting](../01_getting_started/troubleshooting_setup.md)
