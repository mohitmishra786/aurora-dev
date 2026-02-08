# Case Study: Microservices Architecture

Breaking the monolith.

**Last Updated:** February 8, 2026
**Industry:** Logistics

## Challenge

"ShipIt" had a Python Monolith where the `User` service was tightly coupled with `Billing`. Deploying a typo fix took 45 minutes.

## Solution

The **Architect Agent** designed a Domain Driven Design (DDD) migration plan.
1. Identified "Bounded Contexts".
2. **Refactoring Agent** extracted the `Billing` module into a standalone FastAPI service.
3. **DevOps Agent** created Helm charts for independent deployment.

## Results

- **Deploy Time:** Reduced to 5 minutes per service.
- **Reliability:** Billing outage no longer takes down the User login.

## Key Learnings

- **Contract Tests:** We needed PACT tests to ensure the services didn't drift apart.
- **Event Bus:** Switching from REST to RabbitMQ for service communication improved resilience.

## Related Reading

- [Kubernetes Deployment](../08_deployment/kubernetes_deployment.md)
- [Architect Agent](../03_agent_specifications/03_architect_agent.md)
