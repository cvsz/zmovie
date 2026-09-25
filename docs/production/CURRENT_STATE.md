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
