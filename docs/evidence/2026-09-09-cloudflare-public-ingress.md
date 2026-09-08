# Cloudflare public ingress evidence

Date: 2026-09-09 (Asia/Bangkok)

## Status

Operator reported that `zmovie.zeaz.dev` was added to the existing Cloudflare/Terraform stack and applied successfully.

Verified in the operator run:

- a proxied Cloudflare CNAME was added for `zmovie.zeaz.dev`;
- Cloudflare Tunnel ingress routes `zmovie.zeaz.dev` to `http://127.0.0.1:8080`;
- the infrastructure change applied as `1 added, 1 changed, 0 destroyed`;
- a subsequent Terraform plan was a no-op;
- DNS resolution was verified;
- public `GET /api/v2/health` returned HTTP 200;
- public `GET /studio` returned HTTP 200;
- Terraform formatting, validation, and focused tests passed.

## Infrastructure source-of-truth caveat

The Cloudflare resources were applied from the local zworkforce checkout at:

```text
/home/cvsz/platforms/zworkforce/infrastructure/terraform/cloudflare/
```

The operator explicitly reported that pre-existing dirty files were preserved and **no commit or push was made** after the apply.

At the time this evidence file was recorded, the GitHub `cvsz/zworkforce` default branch did not yet contain `infrastructure/terraform/cloudflare/zmovie.tf`, and its committed `main.tf` did not yet include the reported zMovie ingress wiring. Therefore the running Cloudflare configuration is ahead of the GitHub infrastructure source-of-truth.

This is intentionally recorded as:

```text
PUBLIC CLOUDFLARE INGRESS          ✅ operator-verified
PUBLIC HEALTH HTTP 200             ✅ operator-verified
PUBLIC STUDIO HTTP 200             ✅ operator-verified
TERRAFORM APPLY                    ✅ operator-verified
TERRAFORM POST-APPLY NO-OP         ✅ operator-verified
INFRASTRUCTURE COMMITTED/PUSHED    ❌ pending
```

## Required follow-up

Commit only the zMovie-specific Terraform files/hunks from the local zworkforce checkout while preserving unrelated dirty changes. Re-run `terraform fmt`, `terraform validate`, a no-op plan, and the focused tests before pushing.

Do not reconstruct or overwrite the local Terraform changes from this evidence document; the applied local working tree is the authoritative source for the uncommitted delta.

## Security note

Public reachability through Cloudflare does not by itself prove every application route is safe for internet exposure. Keep application authentication enabled, retain the approval gate for external publication, and continue production hardening of any legacy unauthenticated endpoints before treating the service as fully internet-hardened.
