# Test Evidence — zMovie P2 execution (2026-09-24)

> บันทึกผลการตรวจสอบจริง (ภาษาไทย) — อ้างเฉพาะสิ่งที่รันจริง
> ไม่เคลมสิ่งที่ไม่ได้วัด

## 1. Python

| Check | Result |
|---|---|
| `ruff check app.py main.py zmovie_platform tests` | PASS (all checks passed) |
| `unittest discover -s tests` (145 tests) | 143 PASS, 2 ERROR (pre-existing, ดูด้านล่าง) |
| New: `test_studio_cinema` (7) | PASS |
| New: `test_commerce` (9) | PASS |
| New: `test_ticketing` (6) | PASS |
| New: `test_cinema_api` (1) | PASS |
| New: `test_security_regression` (8) | PASS |
| New: `test_ops_probes` (2) | PASS |

**2 errors ที่เป็น pre-existing (ไม่เกี่ยวกับงานรอบนี้):**
`test_bilibili_launch_candidate` + `test_production_gen` import ล้มเหลวเพราะ
`edge_tts` ไม่ได้ติดตั้งใน env นี้ (`ModuleNotFoundError: No module named
'edge_tts'`) — เป็น optional dep ใน `requirements.txt` ที่ CI ติดตั้งให้

**หมายเหตุ compileall:** `__pycache__/` ถูก own โดย root ตั้งแต่ baseline
(`PermissionError` ตอนเขียน `.pyc`) — ไม่ใช่ defect ของโค้ด;
ตรวจสอบ syntax ผ่าน `ruff` + `py_compile` รายไฟล์แทน

## 2. Docker

| Check | Result |
|---|---|
| `docker compose config --quiet` | PASS |
| `docker build -t zmovie:test .` | ไม่รันในเครื่อง (CI `docker` job รันตอน push) |

## 3. PHP / JS / Shell

| Check | Result |
|---|---|
| `php -l` ทุกไฟล์ `wp-plugins/zwp-cinema` + `themes/zwp-cinema` | PASS (no syntax errors) |
| `node --check` (app, studio-preview, hyperframes-studio, durable-worker, product, reels.js) | PASS |
| `shellcheck --severity=warning` สคริปต์ใหม่ 3 ไฟล์ | PASS |

## 4. WordPress REST (production, `https://zmovie.zeaz.dev`)

| Route | Result |
|---|---|
| `/cinema/` | 200 |
| `/cinema/wp-json/` | 200 |
| `/cinema/wp-json/zwpc/v1/feed` | 200 + valid JSON |
| `/cinema/wp-admin/` | 302 (redirect ไป login, ถูกต้อง) |
| `/cinema/wp-json/zwpc/v1/favorites` (anonymous) | 401 (ถูกต้อง) |
| `/cinema/wp-json/zwpc/v1/submit-film` (anonymous) | 401 (ถูกต้อง) |

## 5. License Server E2E

| Check | Result |
|---|---|
| `GET /health` (127.0.0.1:8085) | `healthy` |
| `GET /v1/public-key` | base64url Ed25519 43 chars |
| `POST /v1/activate` (valid key/product/site) | 200 + signed lease (3 parts) |
| `scripts/check-license-api.sh` | OK |

Negative matrix เต็ม (revoked/expired/wrong-site/tampered) อยู่ใน
acceptance backlog — lease verify ผ่าน `license.php` contract แล้ว

## 6. Ticketing concurrency

| Check | Result |
|---|---|
| distinct holds ที่นั่งเดียว (4 threads) | ชนะ 1, ที่เหลือ `taken` (3) |
| confirm ซ้ำ hold เดียว (4 threads) | สำเร็จ 1 |
| hold หมดอายุ + retry | PASS |
| cancel → refund → check-in (+dedup) | PASS |
| idempotent confirm (webhook-style) | `duplicate: True`, id เดียวกัน |

## 7. Commerce sandbox

| Check | Result |
|---|---|
| checkout → confirm → entitlements | PASS |
| webhook HMAC + idempotency (ซ้ำ = ignored, ลายเซ็นผิด = reject) | PASS |
| refund lifecycle (ซ้ำ = reject) | PASS |
| upgrade/downgrade/cancel → revoke | PASS |
| reconciliation balanced/mismatched | PASS |
| live PSP ถูก block (`only sandbox PSP is enabled`) | PASS |
| expiry sweep → revoke | PASS |
| no card storage (`card_number` → reject) | PASS |

## 8. Security regression

8/8 PASS: service-token ปฏิเสธ API JWT, SSRF paths, traversal neutralize,
SQLi inert, webhook/QR replay-tamper, privacy redact + confirm, PBKDF2 hashing

## 9. Probes & ops scripts

| Check | Result |
|---|---|
| `/api/v2/livez` | `alive` (ไม่แตะ DB) |
| `/api/v2/readyz` | `ready` + user count |
| `scripts/smoke-deploy.sh` | โครงสร้างพร้อม (รันเต็มตอน deploy) |
| `scripts/check-backup.sh` | OK (backup ล่าสุดผ่าน integrity) |
| `nginx -t` | syntax ok, test successful |
| `terraform fmt -check -recursive` | PASS (no diff) |
| `terraform validate` | Success (warnings เดิมเรื่อง undeclared vars) |
| `terraform plan` | No changes (infrastructure matches config) |

## 10. Browser smoke (Playwright, Chromium)

| Scenario | Result |
|---|---|
| Desktop 1280×800 `/cinema/` | 200, title `ZeaZ Cinema` |
| Mobile 390×844 + touch `/cinema/` | 200, title `ZeaZ Cinema` |
| Keyboard Tab ×2 | ไม่ crash |
| Feed JSON `?per_page=2` | 200 |

**ยังไม่ทำ (ต้อง staging + ผู้ใช้ทดสอบ):** authenticated flows
(favorites/submit), reduced-motion, screen-reader, Thai/English ทั้ง UI —
ห้ามอ้าง WCAG compliance

## 11. Accessibility / Performance / Load

- **a11y audit:** ยังไม่รัน (ไม่มี axe/Lighthouse) — ไม่เคลม WCAG
- **Perf (observed values, ไม่ใช่ SLO):**
  `/cinema/` ~0.16s, `/cinema/wp-json/` ~0.20s,
  `127.0.0.1:8080/api/v2/health` ~0.73s (วัดครั้งเดียวผ่าน tunnel/localhost)
- **Load tests:** ยังไม่รัน — ต้อง staging แยก + operator approval

## 12. Docs & secret hygiene

| Check | Result |
|---|---|
| `scripts/verify_docs.py` (ไฟล์ของรอบนี้) | PASS ทั้งหมด |
| `verify_docs` pre-existing failures | `docs/MASTER-ZMOVIE-PROMPTS.md:592`, `docs/ZMOVIE_MASTER_P1.md` (8 จุด), `docs/ZMOVIE_MASTER_P2.md` (4 จุด) — เป็น absolute repo paths ใน operator prompt spec เดิม ไม่แตะตาม minimal-diff rule |
| Secret scan (local) | ไม่มี private key / credential จริงใน tracked files; รหัสผ่านเก่าถูก redact เป็น `zeaz-cinema-**** (rotated 2026-09-24)` ใน docs แล้ว |
| `pip-audit -r requirements.txt` | No known vulnerabilities found |

## 13. Backup / Restore / Rollback

ดู `docs/production/BACKUP_RESTORE_EVIDENCE.md`: restore แยก DB 1 วินาที,
ข้อมูลครบ (posts/users/siteurl), rollback plugin/theme สำเร็จ,
backup script มี integrity check + checksum log แล้ว
