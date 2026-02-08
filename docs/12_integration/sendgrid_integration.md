# SendGrid Integration

You've got mail.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Incident Reporting](../10_security/incident_reporting.md)
> - [Configuration](../13_configuration/environment_variables.md)

## Transactional Emails

- **Welcome Email:** Sent on signup.
- **Task Complete:** Summarizes the result.
- **Alert:** Critical system issues.

## Setup

Set `SENDGRID_API_KEY`.
Use Dynamic Templates. Pass JSON data to the template ID.

## Reliability

If SendGrid is down, the email task is retried with Exponential Backoff (via Celery).

## Related Reading

- [Twilio Integration](./twilio_integration.md)
- [Alerting Rules](../09_operations/alerting_rules.md)
