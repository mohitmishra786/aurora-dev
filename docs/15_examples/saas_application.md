# Example: SaaS Application

Building a multi-tenant SaaS with AURORA-DEV.

**Last Updated:** February 8, 2026  
**Audience:** All Users

## Prompt

```markdown
Build a project management SaaS application.

Features:
- Multi-tenant with workspace isolation
- User auth with email/Google OAuth
- Projects with tasks and subtasks
- Team member invitations
- Kanban and list views
- Real-time updates
- Stripe billing integration

Tech: FastAPI, React, PostgreSQL
```

## Generated Structure

```
saas-app/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   └── core/
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── hooks/
│   └── tests/
└── docker-compose.yml
```

## Key Decisions

- JWT + refresh tokens for auth
- Row-level security for multi-tenancy
- WebSockets for real-time
- Stripe webhooks for billing

## Related Reading

- [Project Types](../05_user_guides/project_types.md)
