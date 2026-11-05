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
| `POST /v1/admin/revoke` | admin token | เพิกถอน key แบบถาวร |
| `POST /v1/admin/expire` | admin token | set expiry (lifecycle tests) |
| `POST /v1/admin/features` | admin token | set features (entitlement tests) |

Admin header: `X-License-Admin-Token`. Empty/missing token denies everything.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# create restricted env files from .env.example (0600, root-owned)
```

ก่อนใช้ unit รุ่นที่รันด้วย `cvsz` แทน unit เดิมที่อาจรันด้วย root ให้ย้าย
ownership ของ key directory และไฟล์ state ที่มีอยู่ก่อน:

```bash
# ตั้งตัวแปรให้ตรงกับ EnvironmentFile ของ service
: "${LICENSE_KEYS_DIR:=$HOME/.config/zeaz}"
LICENSE_DB_PATH="${LICENSE_DB_PATH:-$LICENSE_KEYS_DIR/licenses.sqlite3}"
sudo systemctl stop zeaz-license
sudo install -d -o cvsz -g cvsz -m 0700 "$LICENSE_KEYS_DIR" "$(dirname "$LICENSE_DB_PATH")"
for file in \
  "$LICENSE_KEYS_DIR/license_server_private_key.pem" \
  "$LICENSE_KEYS_DIR/license_server_public_key.pem" \
  "$LICENSE_DB_PATH"; do
  if sudo test -f "$file"; then sudo chown cvsz:cvsz "$file"; fi
done
if sudo test -f "$LICENSE_KEYS_DIR/license_server_private_key.pem"; then
  sudo chmod 0600 "$LICENSE_KEYS_DIR/license_server_private_key.pem"
fi
if sudo test -f "$LICENSE_KEYS_DIR/license_server_public_key.pem"; then
  sudo chmod 0644 "$LICENSE_KEYS_DIR/license_server_public_key.pem"
fi
if sudo test -f "$LICENSE_DB_PATH"; then
  sudo chmod 0600 "$LICENSE_DB_PATH"
fi
sudo systemctl daemon-reload
sudo systemctl enable --now zeaz-license
```

Public HTTPS ingress (`https://license.zeaz.dev`) is Nginx + Cloudflare
Tunnel; Terraform source of truth lives in zworkforce
(`license_hostname` / `license_origin` / `cloudflare_dns_record.license`).

## Key and license-state backup / restore

- keypair อยู่ใน `$LICENSE_KEYS_DIR` (`license_server_private_key.pem`,
  `license_server_public_key.pem`); directory ใช้ mode 0700, private key 0600
  และ public key 0644
- สถานะ license แบบถาวรอยู่ใน `$LICENSE_DB_PATH` (ค่าเริ่มต้นคือ
  `$LICENSE_KEYS_DIR/licenses.sqlite3`, mode 0600) ฐานข้อมูลเก็บ SHA-256 digest,
  feature, expiry, revocation และ activation metadata โดยไม่เก็บ license key
  ต้นฉบับ
- สำรอง keypair และ SQLite online backup ไปยัง encrypted storage แบบ offline
  โดยเก็บไว้ใน backup set เดียวกัน
- คืนค่าด้วย permission ตามที่ระบุ แล้ว restart service ตรวจ `GET /v1/public-key`
  ให้ตรงกับ key ที่ WordPress pin ไว้ และยืนยันว่า revocation เดิมยังมีผล
  ห้าม commit key material หรือ license state ลง Git

## Tests

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_license_server -v
```

Contract tests use an ephemeral keypair in a temp `LICENSE_KEYS_DIR`
(no production keys involved).
