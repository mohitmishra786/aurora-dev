# Case Study: Enterprise Integration

Connecting to the mainframe.

**Last Updated:** February 8, 2026
**Industry:** Insurance

## Challenge

"SafeInsure" has a COBOL mainframe for policy calculation. The new Web App needed to talk to it.

## Solution

1. **Integration Agent:** Built a "Legacy Gateway" service that speaks SOAP/XML to the mainframe and exposes REST/JSON to the frontend.
2. **Caching:** Since the mainframe is slow (5s response), we cached policy details in Redis for 24h.

## Results

- **UX:** Instant quotes for returning users (via cache).
- **Modernization:** The frontend team never had to see a line of XML.

## Key Learnings

- **Circuit Breaking:** The mainframe goes down often. We implemented strict circuit breakers to fail fast and show a "Maintenance" page instead of hanging.

## Related Reading

- [Custom Integrations](../12_integration/custom_integrations.md)
- [Redis Operations](../09_operations/redis_operations.md)
