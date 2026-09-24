# Architecture ADR — Cinema boundaries (2026-09-24)

> บันทึกการตัดสินใจสถาปัตยกรรม (ภาษาไทย) — ทางเลือกที่พิจารณาและเหตุผล

## ADR-1: Studio→Cinema เป็น explicit boundary (ไม่ใช่ auto-publish)

- **Context:** Studio render สำเร็จไม่ควรกลายเป็นหนัง public อัตโนมัติ
- **Decision:** state machine `rendered → qc → rights → approval_pending →
  approved → importing → transcoding/poster → editorial → published`
  พร้อม idempotency keys, service-token auth, audit trail
- **Alternatives:** (a) auto-import ทุก render ที่ผ่าน QC — ปฏิเสธเพราะเสี่ยง
  ลิขสิทธิ์/คอนเทนต์ไม่ผ่าน review; (b) ใช้ publish_jobs เดิมของ Bilibili —
  ปฏิเสธเพราะเป็น external-publication domain คนละ approval
- **Consequences:** ต้องมี human 2 จุด (approval + editorial) แลกกับความปลอดภัย

## ADR-2: Commerce เป็น sandbox ใน SQLite (ยังไม่แตะเงินจริง)

- **Context:** ต้องมี membership/paywall foundation โดยไม่เปิด live payments
- **Decision:** `zmovie_platform/commerce/` — plans/subs/ledger/append-only,
  `SandboxPSP` เท่านั้น, webhook HMAC + idempotent, ห้ามเก็บ card data,
  `get_psp("stripe"|...)` raise ทันที
- **Alternatives:** ต่อ Stripe จริงเลย — ปฏิเสธเพราะต้องมี approved
  secret workflow + operator approval + reconciliation ก่อน
- **Consequences:** ทดสอบ lifecycle/refund/reconcile ได้เต็มโดยไม่มีความเสี่ยงเงินจริง

## ADR-3: Ticketing แยก service ไม่ใช้ WordPress user meta

- **Context:** ที่นั่ง/ตั๋วต้องการ transactional guarantees ที่ WP meta ให้ไม่ได้
- **Decision:** core ใน `zmovie_platform/ticketing/` + thin FastAPI service
  `services/cinema-api/`; `UNIQUE(showtime_id, seat_no)` กัน double-sell
  ระดับ DB; `BEGIN IMMEDIATE`; signed QR; hold expiry sweep
- **Alternatives:** เก็บ booking ใน WP user meta — ปฏิเสธเพราะไม่มี constraints,
  ไม่มี atomicity, ปนกับ favorites domain
- **PostgreSQL path:** schema ออกแบบให้ port ได้ (swap connection layer +
  `ON CONFLICT DO NOTHING` ที่มีอยู่แล้ว); SQLite ใช้เฉพาะ local/test

## ADR-4: Nginx `/cinema/` ใช้ root + symlink (ไม่ใช่ alias)

- **Context:** `alias` + `try_files /cinema/index.php` ตกไปโดน default root
  (`/usr/share/nginx/htmlindex.php`) ทำให้ `/cinema/wp-json/` 404
- **Decision:** `root /var/www` + symlink `/var/www/cinema →
  /var/www/zmovie-cinema` + nested PHP-FPM handler
- **Consequences:** `try_files` resolve ถูกต้อง; config versioned เป็น example
  ใน `deploy/nginx/` (live file อยู่บน host, source of truth ของ DNS/tunnel
  อยู่ใน zworkforce Terraform)

## ADR-5: License เป็น Ed25519 short-lease แยกโดเมน

- **Context:** ต้องกัน replay + ใช้ผิด site/product
- **Decision:** Ed25519 sign, lease ≤ 15 นาที, cache ≤ 60 วินาที, pin
  `iss/aud/site/product`, private key อยู่ License Server เท่านั้น
- **Consequences:** revoke มีผลช้าสุด ~16 นาที — ยอมรับได้สำหรับ cinema tier;
  ถ้าต้องการ instant revoke ต้องเพิ่ม denylist check (future work)

## ADR-6: Privacy ลบได้แต่ audit คงอยู่

- **Context:** ผู้ใช้ขอลบบัญชี แต่ audit ต้องสมบูรณ์เพื่อตรวจสอบ
- **Decision:** `export_user_data` redact `password_hash`; `delete_user_data`
  ต้องยืนยันชื่อซ้ำ ลบ rows ระบุตัวตนใน DB แต่เก็บ `audit.jsonl` (ไม่มี secret)
- **Consequences:** audit มี actor name ตกค้าง — บันทึกไว้ใน threat model §3.11
