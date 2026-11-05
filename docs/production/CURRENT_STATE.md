# Current State — zMovie + ZeaZ Cinema (2026-09-25)

> ภาพรวมสถานะปัจจุบัน (ภาษาไทย) — รายละเอียดดู matrix + evidence

- **Repositories:** `cvsz/zmovie@main` (GPG-signed), Terraform/DNS ใน zworkforce
- **Production URLs:** `https://zmovie.zeaz.dev/` (307 → app), `/cinema/` 200,
  `/cinema/wp-json/` 200, `/cinema/wp-json/zwpc/v1/feed` 200
- **License Server:** `127.0.0.1:8085` healthy, Ed25519 leases ใช้งานได้
- **Gates:** ดู `docs/production/FEATURE_MATRIX.md` (P0 VERIFIED ทั้งหมดใน sandbox scope)
- **Evidence:** `docs/production/TEST_EVIDENCE.md`,
  `docs/production/PRODUCTION_CLOSEOUT.md`,
  `docs/production/BACKUP_RESTORE_EVIDENCE.md`,
  `docs/production/ROLLBACK_EVIDENCE.md`
- **Runbooks:** `docs/production/DEPLOYMENT_RUNBOOK.md`,
  `docs/runbooks/CLOUDFLARED_RECOVERY.md`,
  `docs/runbooks/LOOPBACK_BINDING.md`,
  `docs/runbooks/OFFSITE_BACKUP.md`,
  `docs/runbooks/POSTGRES_INTEGRATION.md`,
  `docs/runbooks/WORDPRESS_BACKUP_RESTORE.md`
- **Security:** `docs/security/THREAT_MODEL.md`,
  `docs/security/SUPPLY_CHAIN_POLICY.md`,
  `docs/security/LICENSE_KEY_MANAGEMENT.md`
- **Architecture:** `docs/cinema/ARCHITECTURE_ADR.md`
- **ห้ามเปิดโดยไม่มี approval:** live payments, live ticket sales,
  public auto-publish (ดู FEATURE_MATRIX § backlog)

## สถานะเฉพาะรอบ P5 (2026-09-25)

- Managed Cloudflare connector: **BLOCKED** — รอ `CLOUDFLARE_TUNNEL_TOKEN`
  (manual connectors 2 ตัวยังถือ traffic; public routes ตอบ 200/307 ปกติ)
- Terraform: `fmt`/`validate`/`state list` ผ่าน, lock ค้างรอ recovery approval
- PostgreSQL integration: **VERIFIED** (isolated container 4/4, full suite 178/178)
- Browser acceptance แบบ anonymous: **20/20**; authenticated flows BLOCKED
- Supply chain: SBOM + Trivy + manifest + promotion gate ใน workflow ใหม่
  (รอรันบน hosted CI)
- Bind address: ยัง `0.0.0.0:8080` (UFW DENY เป็น mitigation); loopback เตรียมไว้
  รอ maintenance window

## Source security updates (2026-10-06)

การเปลี่ยนแปลงใน source tree รอบนี้เพิ่ม startup validation สำหรับ bind ที่ไม่ใช่
loopback, จำกัด HTTP bootstrap ให้ใช้ loopback ทั้งฝั่ง bind และ client, ทำ
first-admin insert แบบ atomic, จำกัด OAuth email linking ให้ email ที่ provider
ยืนยันแล้ว, และย้าย OAuth token กลับเข้า Studio ผ่าน URL fragment ที่ถูกลบจาก
address bar หลังบันทึก token นอกจากนี้ License Server ใช้ SQLite state ที่คงอยู่
หลัง restart พร้อม file permissions แบบจำกัด และ WordPress feed จำกัด page size
OAuth บน public host ต้องใช้ `ZMOVIE_BASE_URL` แบบ HTTPS เพื่อไม่อาศัย Host
header จาก request
ผลตรวจ source นี้ไม่ยืนยันว่า production host ได้ deploy หรือ restart แล้ว
