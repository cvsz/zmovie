# License Key Management — ZeaZ License (Ed25519)

> การจัดการคีย์ลายเซ็นใบอนุญาต (ภาษาไทย) — private key อยู่เฉพาะใน
> License Server ที่เชื่อถือได้ ส่วน WordPress ได้รับเฉพาะ public key
> แบบ pin เท่านั้น

## 1. อัลกอริทึมและ Token Contract

- อัลกอริทึม: **Ed25519 (EdDSA)** ตรวจด้วย `sodium_crypto_sign_verify_detached`
- Header: `{alg: "EdDSA", kid, typ: "JWT"}` — `kid` ระบุรอบการ rotate
- Claims: `iss="zeaz-license"`, `aud` ต่อ product (เช่น `zmovie`),
  `site` (origin), `product`, `sub` (key), `activation_id`,
  `features[]`, `iat`, `nbf`, `exp`
- อายุ lease ≤ 15 นาที (`exp - iat ≤ 900`), skew ±30 วินาที,
  cache ฝั่ง WordPress ≤ 60 วินาที
- ตรวจ `site/product/audience` ทุกครั้ง — ผิดที่ใด fail-closed

## 2. ที่เก็บคีย์

| คีย์ | ที่อยู่ | ใครเข้าถึงได้ |
|---|---|---|
| Private signing key | License Server env/host เท่านั้น (`license_server_private_key.pem`, chmod 600) | License Server process เท่านั้น |
| Public verify key | `wp-config.php: ZEAZ_LICENSE_PUBLIC_KEY` (base64url, pin นอกระบบ) + `/v1/public-key` | WordPress + สาธารณะ (verify only) |
| License key (`ZEAZ_LICENSE_KEY`) | secret env ของ site | WordPress server เท่านั้น |

**ห้าม:** commit private key / license key / DB password ลง git,
พิมพ์ secret ลง log/issue/PR, ฝัง key ใน HTML/JS, ใช้ key เดียวข้าม product

## 3. การ Rotate คีย์

1. สร้าง Ed25519 คู่ใหม่ใน License Server (เก็บ private ใหม่แบบ 600)
2. เผยแพร่ public key ใหม่พร้อม `kid` ใหม่ (รองรับ verify 2 `kid` ช่วงเปลี่ยนผ่าน)
3. อัปเดต `ZEAZ_LICENSE_PUBLIC_KEY` + `kid` ใน `wp-config.php` ผ่าน secret workflow
4. ตรวจสอบ activation จริง (valid/invalid/revoked/expired/wrong-site)
5. เก็บ private key เก่าแบบ revoke หลัง lease สุดท้ายหมดอายุ (≤ 15 นาที + cache)
6. บันทึก audit: `kid` เก่า/ใหม่, เวลา, ผู้ดำเนินการ (redacted)

## 4. Incident ที่เคยเกิด (2026-09-24) และบทเรียน

- **เหตุ:** DB password `zeaz-cinema-2026` หลุดใน `docs/production/FINAL_READINESS_REPORT.md`
  ที่เข้าถึงได้สาธารณะ (public report)
- **การตอบสนอง:** ถือว่า compromised ทันที → สร้างรหัสผ่านใหม่
  high-entropy → อัปเดต MariaDB + `wp-config.php` + `.env` →
  ตรวจ WordPress เชื่อมต่อได้ → แทนค่าด้วย `***ROTATED***` →
  บันทึก redacted evidence → เพิ่ม CI secret scanning
- **บทเรียน:** ห้ามใส่ค่าจริงใน production report, backup script ต้องใช้
  `--defaults-file` (ไม่ใช่ `--password=` ใน CLI), review ทุกไฟล์ก่อน push

## 5. การตรวจสอบประจำ

- `test.yml`: `pip-audit`, `ruff`, `shellcheck`, PHP lint
- `secret-scan.yml`: สแกน `BEGIN PRIVATE KEY`, รหัสผ่านตัวอย่างที่เคยหลุด,
  `--password=` ในสคริปต์, `.env` หลุดเข้า git
- ทดสอบ E2E: valid/invalid/revoked/expired/wrong-product/wrong-site/
  tampered-signature/wrong-public-key/unsupported-algorithm/missing-entitlement
- ตรวจว่าไม่มี secret ใน HTML, git history ใหม่, application log

## 6. อ้างอิง

- `wp-plugins/zwp-cinema/includes/license.php`
- `docs/services/LICENSE_SERVER.md`
- `docs/security/THREAT_MODEL.md` (§3.6, §3.9)
- `docs/production/FINAL_READINESS_REPORT.md` (§11 Credential Exposure)
