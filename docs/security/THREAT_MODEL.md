# Threat Model — zMovie + ZeaZ Cinema

> เอกสารนี้อธิบาย threat model ระดับสถาปัตยกรรม (ภาษาไทย) สำหรับ
> zMovie Studio, License Server, WordPress Cinema, Commerce sandbox
> และ Ticketing API แยก domain

## 1. ขอบเขต (Scope)

**ในขอบเขต:**
- zMovie FastAPI (`/api/v2`): auth, project ownership, render queue,
  media preview, publication approval, Studio→Cinema import
- License Server ภายใน: Ed25519 signing, lease 15 นาที
- WordPress `zwp-cinema`: film catalog, REST feed, favorites,
  creator submission (moderated), license verification
- Commerce sandbox: PSP abstraction, webhook, ledger, refund
- Ticketing API แยก: holds, atomic reservations, signed QR, check-in

**นอกขอบเขต (ยังไม่เปิด):** live payments, live ticket sales,
public Sto→Cinema auto-publish, Remote GPU ที่ไม่ผ่าน approval

## 2. Actors และ Trust Boundaries

| Actor | Trust | หมายเหตุ |
|---|---|---|
| Anonymous | ไม่เชื่อถือ | อ่านได้เฉพาะ public feed/health |
| Member/Creator | เชื่อถือบางส่วน | ผ่าน auth + ownership + license entitlement |
| Admin/Editor | เชื่อถือสูง | อนุมัติ publish, editorial, refund |
| Cinema service | เชื่อถือแบบจำกัด | service token แยกจาก user JWT |
| PSP sandbox | ไม่เชื่อถือ | ตรวจ HMAC ทุก webhook, idempotent |
| Staff หน้างาน | เชื่อถือบางส่วน | check-in ด้วย QR ที่ verify ลายเซ็น |

**แยก authorization domains:** payment / creator licensing /
film-distribution rights / ticketing เป็นคนละ domain — token
ข้าม domain ใช้ไม่ได้ (เช่น API JWT ใช้แทน cinema service token ไม่ได้)

## 3. Threats สำคัญและการบรรเทา

### 3.1 Authentication / Session
- **Threat:** token Theft, session fixation, brute force
- **Mitigation:** HMAC-SHA256 purpose-bound tokens (`aud` แยก api/media-preview),
  TTL จำกัด, login/bootstrap rate limit ต่อ client IP (429 + Retry-After),
  PBKDF2 250k สำหรับรหัสผ่าน, admin bootstrap ครั้งเดียว

### 3.2 RBAC / Object-level authorization
- **Threat:** IDOR — เข้าถึง project/import/reservation ของคนอื่น
- **Mitigation:** `require_project` (owner หรือ admin), publish job ผูก project,
  reservation ผูก holder_ref, approve/editorial ต้อง admin,
  ทดสอบใน `test_security_boundaries.py` + `test_security_regression.py`

### 3.3 REST nonce / CSRF (WordPress)
- **Threat:** cross-site request เปลี่ยน favorites/submission
- **Mitigation:** cookie auth ต้องมี REST nonce, งานเขียนต้อง login,
  submission ต้องมี `cinema.creator` entitlement, publish ต้อง moderator

### 3.4 SSRF / Path traversal / Upload
- **Threat:** ดึง URL ภายนอกโดยไม่ตั้งใจ, `../` หลุด root, อัปโหลดอันตราย
- **Mitigation:** รับเฉพาะ managed paths (`validate_managed_asset_path`),
  `safe_project_path` กัน traversal, video URL ต้อง https + mp4/webm,
  ห้ามประมวลผล remote media URL โดยไม่มี SSRF review, ไม่อ่านไฟล์นอก root

### 3.5 XSS / SQL injection
- **Threat:** script injection ผ่าน title/content, SQLi ผ่าน input
- **Mitigation:** escape output (`esc_html/esc_url`), parameterized queries
  ทุกจุด (ไม่มี string interpolation ใน SQL), ทดสอบ regression

### 3.6 License replay
- **Threat:** เอา lease เก่ามาใช้ซ้ำ, แก้ claims, ใช้ผิด site/product
- **Mitigation:** Ed25519 verify + `iss/aud/site/product` pin,
  `iat/nbf/exp` ตรวจ skew ±30s, lease ≤ 15 นาที, cache ≤ 60 วินาที,
  `activation_id` ผูกการใช้งาน

### 3.7 Webhook forgery / Replay
- **Threat:** ปลอม PSP webhook, ส่ง event ซ้ำให้ double-credit
- **Mitigation:** HMAC-SHA256 verify ก่อนประมวลผล, `event_id` UNIQUE
  (ซ้ำ = `duplicate_ignored`), ledger idempotency key UNIQUE

### 3.8 Ticketing fraud / Double-selling
- **Threat:** ขายที่นั่งซ้ำ, hold ไม่หมดอายุ, QR ปลอม, check-in ซ้ำ
- **Mitigation:** `UNIQUE(showtime_id, seat_no)` ระดับ DB,
  `BEGIN IMMEDIATE` transactions, hold หมดอายุ + sweep,
  QR HMAC มี `exp`, check-in dedup, cancel/refund เป็น state machine

### 3.9 Secrets management
- **Threat:** secret หลุดลง git/log/backup (เคยเกิดจริงกับ DB password)
- **Mitigation:** secret ผ่าน env/secret manager เท่านั้น, ห้าม hard-code,
  CI secret-scan, backup script ใช้ `--defaults-file` (chmod 600),
  incident response: rotate ทันที + redacted evidence (ดู Phase 1)

### 3.10 Dependencies / Containers
- **Threat:** vulnerable deps, ภาพ container มีช่องโหว่
- **Mitigation:** `pip-audit` ใน CI, Dependabot, `docker build` ใน CI,
  นโยบายอัปเดตใน `docs/production/DEPLOYMENT_RUNBOOK.md`

### 3.11 Audit logging / Privacy
- **Threat:** ปฏิเสธความรับผิดไม่ได้, เก็บข้อมูลเกินจำเป็น
- **Mitigation:** audit log ทุก publication/commerce/ticketing/privacy event,
  export ลบ `password_hash`, ลบบัญชีต้องยืนยันชื่อซ้ำ,
  audit file เก็บไว้เพื่อความสมบูรณ์ของบันทึก

## 4. Residual risks (ที่เหลืออยู่)

1. Playwright browser state ของ Bilibili เป็น credential — ต้องจัดการแบบ secret
2. WordPress E2E (browser/keyboard/a11y) ยังไม่รัน — ห้ามอ้าง WCAG จนกว่าจะวัดจริง
3. Live payments/ticket sales ยังไม่ได้รับ approval — sandbox เท่านั้น
4. Cloudflare Tunnel/Access config อยู่นอก repo นี้ — ต้อง reconcile ผ่าน Terraform source of truth

## 5. อ้างอิงการตรวจสอบ

- `tests/test_security_boundaries.py`, `tests/test_security_regression.py`
- `tests/test_commerce.py` (webhook/replay/refund), `tests/test_ticketing.py` (concurrency)
- `.github/workflows/secret-scan.yml`, `test.yml` (ruff/pip-audit/shellcheck)
- `docs/security/LICENSE_KEY_MANAGEMENT.md`
