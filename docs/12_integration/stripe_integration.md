# Stripe Integration

Show me the money.

**Last Updated:** February 8, 2026
**Audience:** Developers

> **Before Reading This**
>
> You should understand:
> - [Billing Configuration](../13_configuration/feature_flags.md)
> - [API Reference](../07_api_reference/rest_api.md)

## Usage Based Billing

We bill customers based on **Token Usage**.
1. Agent finishes run.
2. System calculates tokens * price.
3. System sends `usage_record` to Stripe Metered Billing API.

## Subscriptions

We support tiered plans (Starter, Pro, Enterprise).
Webhooks listen for `checkout.session.completed` to provision the account.

## Setup

Set `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`.

## Related Reading

- [Managing Costs](../05_user_guides/managing_costs.md)
- [ROI Analysis](../18_business/roi_analysis.md)
