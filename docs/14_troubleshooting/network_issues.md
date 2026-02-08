# Network Issues

DNS is always the problem.

**Last Updated:** February 8, 2026
**Audience:** Network Engineers

> **Before Reading This**
>
> You should understand:
> - [Network Security](../10_security/network_security.md)
> - [Infrastructure Diagram](../21_diagrams/architecture/infrastructure_diagram.mmd)

## DNS Resolution Failure

*Error:* `generic: temporary failure in name resolution`.
*Cause:* CoreDNS issues in K8s.
*Fix:* Check `kubectl get pods -n kube-system`.

## Latency Spikes

*Cause:* Cross-region traffic.
*Fix:* Ensure App and DB are in the same Availability Zone (AZ).

## Firewall Drops

*Symptom:* Random timeouts.
*Cause:* Security Group blocking Ephemeral Ports.
*Fix:* Allow established TCP traffic.

## Related Reading

- [Network Security](../10_security/network_security.md)
- [Certificate Management](../09_operations/certificate_management.md)
