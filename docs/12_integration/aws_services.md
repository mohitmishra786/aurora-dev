# AWS Services

The cloud toolbox.

**Last Updated:** February 8, 2026
**Audience:** Architects

> **Before Reading This**
>
> You should understand:
> - [Cloud AWS](../08_deployment/cloud_aws.md)
> - [Deployment Flow](../21_diagrams/flows/deployment_flow.mmd)

## S3 (Storage)

Used for all blob storage:
- User uploads.
- Agent generated artifacts (PDFs, Images).
- Database backups.

## Bedrock (AI)

We can switch the LLM provider to AWS Bedrock (Claude 3 on AWS) for data residency compliance.

## SQS (Queues)

Alternative to Redis for the job queue. More durable, less maintenance.

## Related Reading

- [Cloud AWS](../08_deployment/cloud_aws.md)
- [Queue Configuration](../13_configuration/queue_configuration.md)
