# Cloudflare and Terraform Ownership

This repository does not ship Cloudflare Terraform. Public DNS records and tunnel
ingress must have exactly one owning repository, and that repository is the only
place they may be declared.

## The Rule

| | |
|---|---|
| **Owner** | `cvsz/zworkforce` (the infrastructure repository for edge configuration) |
| **Scope** | Every public DNS record (`zmovie.zeaz.dev`, `license.zeaz.dev`) and every shared-tunnel ingress route |
| **This repository may** | Declare application code, containers, runtime configuration, and Nginx reverse-proxy config |
| **This repository must not** | Contain `cloudflare_dns_record`, `cloudflare_tunnel`, `cfargotunnel.com`, or per-project Terraform for Cloudflare |

## Worked Example

The owning repository (`cvsz/zworkforce`) serves every hostname under a single zone and a single tunnel using Terraform.

### Requesting a Hostname

1. Confirm the service is running and healthy on a loopback port on the target host.
2. Create a feature branch in **cvsz/zworkforce** and add the declaration there:
   - A hostname variable validated as a subdomain of the zone
   - An origin variable validated to a loopback address, pinned to the reviewed port
   - A `cloudflare_dns_record` pointing at the shared tunnel target
   - A matching entry in the tunnel ingress list
   - A URL output
3. If the record already exists, **adopt it** via `terraform import`:
   ```bash
   terraform import cloudflare_dns_record.<name> "<zone_id>/<record_id>"
   ```
   Importing is always correct. Creating will fail with a duplicate-record error; deleting first would briefly take the hostname offline.
4. Run `terraform plan` and confirm `0 to destroy`. A plan proposing destruction of unrelated resources means the branch is based on stale config. Stop and rebase; do not apply.
5. Open a pull request and let it clear review and required checks.
6. **Only after the pull request merges**, apply the plan on the branch that is now `main`, then verify the public route and re-check other hostnames on the same tunnel for regressions.

### Why Apply Comes After Merge

A shared tunnel also serves production hostnames that this change does not mention, so a careless ingress edit has a wider blast radius than the new hostname. Reviewing only the rendered diff, while the live tunnel is still untouched, is the point at which a mistake is still free.

### Keeping One Ingress List

If the owning repository manages the tunnel config in Terraform, do not write the hostname list twice. A copy maintained by hand will drift silently: DNS records exist, but requests fall through to the terminal catch-all route and return `http_status:404`.

Declare routes once, in a shared local value in the owning repository, and read it from both the managed tunnel config and the operator-facing output.

### If zMovie Needs a Separate Tunnel

Do not create one by default. A separate tunnel means another connector, its own credential, and another thing to keep alive across reboots. Raise it first, and expect to justify why the shared tunnel is not sufficient.

## Local Development

Terraform is not run from this project. `terraform plan` requires the operator credentials that live in the owning repository's host configuration, and the state is not part of this repository.

## Current Hostnames (managed in cvsz/zworkforce)

| Hostname | Tunnel Target | Status |
|----------|---------------|--------|
| `zmovie.zeaz.dev` | `http://127.0.0.1:8080` (via Nginx) | Active |
| `license.zeaz.dev` | `http://127.0.0.1:8085` (via Nginx) | Active |

## Nginx Configuration (this repository)

This repository provides Nginx site templates under `deploy/nginx/` for the reverse-proxy layer that terminates TLS from Cloudflare and forwards to the local application ports. These are **not** Cloudflare configuration — they are local HTTP routing.