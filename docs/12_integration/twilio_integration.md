# Twilio Integration

Don't text and drive.

**Last Updated:** February 8, 2026
**Audience:** DevOps

> **Before Reading This**
>
> You should understand:
> - [SendGrid Integration](./sendgrid_integration.md)
> - [Alerting Rules](../09_operations/alerting_rules.md)

## SMS Alerts

Used primarily for **Critical Severity** alerts (PagerDuty fallback).
"AURORA CRITICAL: Database CPU at 99%."

## 2FA

We use Twilio Verify API for sending OTPs (One Time Passwords) during login.

## Setup

Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_FROM_NUMBER`.

## Related Reading

- [SendGrid Integration](./sendgrid_integration.md)
- [Authentication](../10_security/authentication_authorization.md)
