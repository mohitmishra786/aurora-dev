# Self-Hosted Deployment

For the brave.

**Last Updated:** February 8, 2026
**Audience:** SysAdmins

> **Before Reading This**
>
> You should understand:
> - [System Requirements](../01_getting_started/system_requirements.md)
> - [Docker Deployment](./docker_deployment.md)

## Bare Metal

You can run AURORA-DEV on a single Ubuntu 22.04 server.
Specs: 8 CPU, 32GB RAM, 100GB SSD.

## Systemd

We provide systemd units in `deploy/systemd`.
```bash
cp deploy/systemd/aurora.service /etc/systemd/system/
systemctl enable aurora
systemctl start aurora
```

## Reverse Proxy

Use Nginx or Caddy.
Caddyfile example:
```
aurora.example.com {
    reverse_proxy localhost:8000
}
```

## Security

Ensure `UFW` allows only ports 80, 443, and 22.
Do NOT expose port 5432 (Postgres) to the internet.

## Related Reading

- [Docker Deployment](./docker_deployment.md)
- [Backup & Restore](./backup_restore.md)
