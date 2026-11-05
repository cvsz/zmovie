# ZeaZ License Server

## Overview
First-party License Server built with FastAPI + PostgreSQL + Ed25519 signing.

## Location
`services/license-server/` (repo-relative)

## Running
```bash
cd services/license-server
python3 server.py
```
Server runs on `127.0.0.1:8085`.

## Endpoints
- `GET /health` — Health check
- `GET /v1/public-key` — Returns public verification key (base64url Ed25519)
- `POST /v1/activate` — Activate a license key, returns signed JWT lease
- `GET /v1/leases/{activation_id}` — Get lease details

## Token Contract (matches license.php expectations)
- Algorithm: EdDSA
- Header: `{alg: "EdDSA", kid: "e58bc8616e5d12cf", typ: "JWT"}`
- Claims: `iss`, `aud`, `site`, `sub`, `activation_id`, `iat`, `nbf`, `exp`, `features`
- `exp - iat <= 900` (15 minutes)
- `iss` = "zeaz-license", `aud` = "zmovie"

## Key Storage
- Private key: `~/.config/zeaz/license_server_private_key.pem`
- Public key: `~/.config/zeaz/license_server_public_key.pem`
- Public key (base64url): `~/.config/zeaz/public-key.pem`
- Directory mode: `0700`; private/public key modes: `0600` / `0644`
- Durable license database: `~/.config/zeaz/licenses.sqlite3` (mode `0600`)

## License Key
- Supply `LICENSE_SEED_KEYS` through the restricted service environment file.
- ห้ามบันทึกค่า license key ในเอกสารหรือ repository
- Product: zmovie
- Features: catalog, favorites, submit_film, creator_submission, license_verification

ฐานข้อมูล license เก็บ feature, expiry, revocation และ activation metadata
โดยเก็บ SHA-256 digest แทน key ต้นฉบับ ระบบสำรองข้อมูลด้วย SQLite online
backup ใน `scripts/backup-dr.sh`; เก็บ backup คู่กับ signing key ในที่เก็บ
เข้ารหัสและจำกัดสิทธิ์
