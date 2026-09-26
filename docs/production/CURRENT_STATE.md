# Current State — zMovie + ZeaZ Cinema (2026-09-24)

> ภาพรวมสถานะปัจจุบัน (ภาษาไทย) — รายละเอียดดู matrix + evidence

- **Repositories:** `cvsz/zmovie@main` (GPG-signed), Terraform/DNS ใน zworkforce
- **Production URLs:** `https://zmovie.zeaz.dev/` (307 → app), `/cinema/` 200,
  `/cinema/wp-json/` 200, `/cinema/wp-json/zwpc/v1/feed` 200
- **License Server:** `127.0.0.1:8085` healthy, Ed25519 leases ใช้งานได้
- **Gates:** ดู `docs/production/FEATURE_MATRIX.md` (P0 VERIFIED ทั้งหมดใน sandbox scope)
- **Evidence:** `docs/production/TEST_EVIDENCE.md`,
  `docs/production/BACKUP_RESTORE_EVIDENCE.md`,
  `docs/production/ROLLBACK_EVIDENCE.md`
- **Runbooks:** `docs/production/DEPLOYMENT_RUNBOOK.md`,
  `docs/runbooks/WORDPRESS_BACKUP_RESTORE.md`
- **Security:** `docs/security/THREAT_MODEL.md`,
  `docs/security/LICENSE_KEY_MANAGEMENT.md`
- **Architecture:** `docs/cinema/ARCHITECTURE_ADR.md`
- **ห้ามเปิดโดยไม่มี approval:** live payments, live ticket sales,
  public auto-publish (ดู FEATURE_MATRIX § backlog ข้อ 6)
