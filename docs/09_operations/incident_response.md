# Incident Response

When things go boom.

**Last Updated:** February 8, 2026
**Audience:** Incident Commanders

> **Before Reading This**
>
> You should understand:
> - [Incident Report Template](../22_templates/incident_template.md)
> - [Alerting Rules](./alerting_rules.md)

## The Process (SEV-1)

1. **Acknowledge:** "I am investigating." (Stop the pager).
2. **Assess:** Is it a false alarm? Is it affecting customers?
3. **Communicate:** Update Status Page. "We are investigating an issue with..."
4. **Mitigate:** Rollback the last deployment. Turn on the "Maintenance Mode" switch.
5. **Analyze:** Once stable, find root cause. (Not during the fire).

## Roles

- **Incident Commander:** Runs the call. Makes decisions.
- **Scribe:** Writes down timeline.
- **Subject Matter Expert:** Types the commands.

## Post-Mortem

Within 24 hours, write a Blameless Post-Mortem using the template.
Focus on *process* failure, not *human* failure. "Why did the test suite allow this bug?" Not "Why did Bob write the bug?"

## Related Reading

- [Incident Report Template](../22_templates/incident_template.md)
- [Runbook Template](../22_templates/runbook_template.md)
