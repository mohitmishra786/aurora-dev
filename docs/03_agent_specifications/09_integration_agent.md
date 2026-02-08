# Integration Agent

The diplomat connecting your system to the outside world.

**Last Updated:** February 8, 2026
**Audience:** Developers, DevOps

> **Before Reading This**
>
> You should understand:
> - [Integration Template](../22_templates/integration_template.md)
> - [Custom Integrations](../12_integration/custom_integrations.md)
> - [Base Agent](./00_base_agent.md)

## The Bridge Builder

Modern applications are rarely self-contained. They are a patchwork of third-party APIs: Stripe for money, Twilio for texts, SendGrid for emails, AWS S3 for files. The Integration Agent manages these volatile relationships.

It is responsible for reading external API documentation (usually via the `Research Agent`), generating client wrappers, and ensuring that failures in external systems don't cascade into your core application.

It acts as the "translation layer." Your app shouldn't know that Stripe uses `snake_case` JSON while your app uses `camelCase` objects. The Integration Agent builds the adapter that converts between the two worlds.

"The only thing guaranteed about a third-party API is that it will change without notice." — Veteran Engineer. This agent plans for that update.

## Core Responsibilities

### 1. SDK Generation / Wrapping
It creates a clean Python/TypeScript interface for the external service.
- **Input:** "Integrate OpenAI API."
- **Output:** A `OpenAIClient` class with typed methods like `chat_completion()`, handling authentication and retries internally.

### 2. Webhook Handling
It builds the endpoints that receive data *from* external services. It verifies cryptographic signatures (HMAC) to ensure the data is essentially from Stripe/GitHub and not an attacker.

### 3. Resilience Patterns
It automatically applies Circuit Breakers and Exponential Backoff strategies. If the external API starts returning 500 errors, the agent's code stops hammering it and waits, preventing your system from hanging.

## Resilience Flow

Here is how the Integration Agent designs a robust external call.

```mermaid
graph TD
    App[Application Logic] --> Call[Call External Method]
    Call --> Circuit{Circuit Status}
    
    Circuit -->|Open (Broken)| Error[Fast Fail Error]
    
    Circuit -->|Closed (OK)| Request[HTTP Request]
    Request --> Provider[External Service]
    
    Provider -->|200 OK| Success[Return Data]
    Provider -->|5xx Error| Fail[Record Failure]
    
    Fail --> Retry{Retry Rule}
    Retry -->|Count < 3| Wait[Backoff Wait]
    Wait --> Request
    
    Retry -->|Count >= 3| Trip[Trip Circuit]
    Trip --> Error
    
    classDef external fill:#f87171,stroke:#b91c1c,color:white;
    class Provider external;
```

## Tools and Configuration

This agent needs access to external docs and local network configs.

```yaml
# aurora.yaml
agents:
  integration:
    model: claude-3-sonnet-20240229
    temperature: 0.2
    tools:
      - read_url        # To read API docs
      - read_file
      - write_file
      - generate_sdk    # Custom internal tool
    context_window:
      include:
        - "src/backend/core/integrations/*.py"
        - "docs/external_api_specs/*.yaml"
```

## Best Practices

### "The Anti-Corruption Layer"
The agent never lets external data structures leak into the core domain.
- *External:* `{"cust_id_99": "Steve", "payment_status_code": 1}`
- *Internal:* `User(id="Steve", payment_status=Status.PAID)`
It maps the messy external reality to the clean internal ideal.

### "Secrets are Secret"
The agent never checks API keys into code. It references `os.getenv("STRIPE_KEY")` and updates the `.env.example` file to remind developers to set it.

### "Mock Everything"
For testing, the agent generates a `MockClient` that mimics the external service. This allows unit tests to run without an Internet connection and without billing your credit card.

## Common Failure Modes

### 1. API Version Drift
The external API changes its response format.
*Fix:* The Integration Agent writes contract tests (using PACT or similar concepts) that run nightly against the real API to detect breaking changes early.

### 2. Timeout Traps
Default HTTP clients often have no timeout. The app hangs forever if the external server stalls.
*Fix:* The agent enforces strict timeouts (e.g., `timeout=5.0`) on all network calls.

## Related Reading

- [Integration Template](../22_templates/integration_template.md)
- [Security Model](../10_security/security_model.md) - How to handle those API keys.

## What's Next

- [Test Engineer](./10_test_engineer.md)
