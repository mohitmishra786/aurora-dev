# Example: REST API

Building a production REST API with AURORA-DEV.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Prompt

```markdown
Build a REST API for an e-commerce platform.

Features:
- Product catalog with categories
- User accounts and auth
- Shopping cart
- Order management
- Payment processing (Stripe)
- Admin endpoints
- Rate limiting

Tech: FastAPI, PostgreSQL
```

## Generated Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /products | List products |
| POST | /cart | Add to cart |
| POST | /orders | Create order |
| POST | /payments | Process payment |

## Quality Metrics

- 92% test coverage
- OpenAPI documentation
- JWT authentication
- Rate limiting configured

## Related Reading

- [Backend Agent](../03_agent_specifications/06_backend_agent.md)
