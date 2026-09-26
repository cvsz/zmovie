# ZeaZ License Server

First-party Ed25519 license issuance for `zmovie` (short-lived signed leases).

## Token contract (matches `wp-plugins/zwp-cinema/includes/license.php`)

- Algorithm `EdDSA`, header `{alg, kid, typ: "JWT"}`
- Claims `iss="zeaz-license"`, `aud="zmovie"`, `site`, `product`, `sub`,
  `activation_id`, `features[]`, `iat`, `nbf`, `exp` (`exp - iat <= 900`)
- Canonical entitlement: `cinema.creator` (+ legacy aliases)

## Endpoints

| Method + path | Auth | Purpose |
|---|---|---|
| `GET /health` | none | liveness |
| `POST /v1/activate` | rate-limited (20/min/IP) | issue lease |
| `GET /v1/public-key` | none | pinned base64url Ed25519 key |
| `GET /v1/leases/{id}` | admin token | introspection (edge-denied publicly) |
| `POST /v1/admin/revoke` | admin token | revoke key (in-memory) |
| `POST /v1/admin/expire` | admin token | set expiry (lifecycle tests) |
| `POST /v1/admin/features` | admin token | set features (entitlement tests) |

Admin header: `X-License-Admin-Token`. Empty/missing token denies everything.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# create restricted env files from .env.example (0600, root-owned)
sudo systemctl daemon-reload
sudo systemctl enable --now zeaz-license
curl -s http://127.0.0.1:8085/health
```

Public HTTPS ingress (`https://license.zeaz.dev`) is Nginx + Cloudflare
Tunnel; Terraform source of truth lives in zworkforce
(`license_hostname` / `license_origin` / `cloudflare_dns_record.license`).

## Key backup / restore

- Active keypair: `$LICENSE_KEYS_DIR` (`license_server_private_key.pem`,
  `license_server_public_key.pem`). Private key is 0600.
- Back up both files to offline encrypted storage on rotation.
- Restore: place files back with 0600/0644, restart the service, verify
  `GET /v1/public-key` still matches the WordPress-pinned key before
  serving traffic. Never commit key material to Git.

## Tests

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_license_server -v
```

Contract tests use an ephemeral keypair in a temp `LICENSE_KEYS_DIR`
(no production keys involved).
