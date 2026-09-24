# Feature Matrix — requirements to implementation (2026-09-24)

> สถานะตามหลักฐานจริง: VERIFIED = มี check ผ่านตาม scope ที่ระบุ,
> IMPLEMENTED_NOT_VERIFIED = มีโค้ดแต่ยังไม่ผ่าน gate,
> MISSING = ยังไม่มี, BLOCKED = ติด external dependency/approval

## P0 — Critical

| Feature | Status | Location | Evidence |
|---|---|---|---|
| Credential rotation (exposed DB password) | VERIFIED | MariaDB `zmovie_cinema`, `wp-config.php`, `~/.my.cnf`, report redacted | WP connects, no active secret in tracked files, secret-scan CI |
| WordPress REST via `/cinema` prefix | VERIFIED | `deploy/nginx/zmovie-cinema.conf.example`, `/var/www/cinema` symlink | `/cinema/` 200, `/cinema/wp-json/` 200, `zwpc/v1/feed` 200 |
| Cloudflare DNS + tunnel ingress | VERIFIED | zworkforce Terraform (`cloudflare_dns_record.zmovie`) | `validate` ok, `plan` no changes, HTTPS 200 |
| License Server + signed-lease integration | VERIFIED | `services/license-server/`, `license.php` contract | activate 200, Ed25519 3-part JWT, negative tests pending full matrix |
| Isolated restore drill | VERIFIED | `docs/production/BACKUP_RESTORE_EVIDENCE.md` | 1s restore, counts + siteurl validated |
| Rollback drill (plugin/theme) | VERIFIED | `docs/production/ROLLBACK_EVIDENCE.md` | backup/extract/boot checks pass |
| Studio→Cinema boundary (no auto-publish) | VERIFIED | `zmovie_platform/studio_cinema.py`, `cinema_import_routes.py` | 7 unit tests (dup/missing/failed/reject/happy-path/token) |
| Backup integrity + failure alerts | VERIFIED | backup script + `scripts/check-backup.sh` | integrity check pass, cron-ready exit codes |

## P1 — Should fix

| Feature | Status | Blocker / Next |
|---|---|---|
| Commerce sandbox (plans/subs/ledger/webhooks/refunds) | VERIFIED (sandbox) | `zmovie_platform/commerce/` — 9 tests; live PSP BLOCKED (needs approved secret workflow + operator approval) |
| Ticketing API (holds/atomic seats/QR/check-in) | VERIFIED (sandbox) | `zmovie_platform/ticketing/` + `services/cinema-api/` — 7 tests; live sales BLOCKED (payment/refund/legal/ops acceptance) |
| Security audit + privacy export/delete | VERIFIED | `docs/security/THREAT_MODEL.md`, 8 regression tests; full pentest NOT_APPLICABLE this round |
| Probes + smoke + runbooks | VERIFIED | `/livez`, `/readyz`, 3 ops scripts, 2 runbooks; PagerDuty NOT_APPLICABLE |
| Playwright smoke (desktop/mobile/keyboard/feed) | VERIFIED (smoke) | Authenticated E2E + reduced-motion + screen-reader MISSING |
| docs hygiene (`verify_docs` new files, secret-scan) | VERIFIED | Pre-existing P1/P2 prompt path warnings remain (out of scope) |

## P2 — Nice to have

| Feature | Status | Blocker / Next |
|---|---|---|
| Media pipeline (transcode/poster/CDN/signed media) | IMPLEMENTED_NOT_VERIFIED | Hooks exist in Studio→Cinema; real-model FFprobe evidence needs operator weights/host |
| Membership lifecycle UI + invoices | IMPLEMENTED_NOT_VERIFIED | Core + API done; WP/member UI MISSING |
| Accessibility audit (WCAG 2.2 AA) | MISSING | No axe/Lighthouse run — do not claim compliance |
| Performance/load SLOs | MISSING | Observed timings only (TEST_EVIDENCE §11); SLOs need operator approval |
| Staging env + CD pipeline | MISSING | Docs define contract; infra in zworkforce scope |
| Container image scan / SBOM signing | MISSING | `pip-audit` done; image scan pending |

## Dependency-ordered backlog (remaining)

1. P0: เต็ม matrix license negative tests ผ่าน License Server จริง (staged WP)
2. P1: Playwright authenticated E2E (favorites/submit) บน staging
3. P1: a11y audit + perf/load บน staging (กำหนด SLO กับ operator ก่อน)
4. P2: member UI + invoices + CDN/signed media
5. P2: staging env + CD + image scan/SBOM
6. BLOCKED จนกว่าจะ approval: live payments, live ticket sales, public auto-publish
   (ห้ามเปิดทั้งสามอย่างโดยไม่มี payment/refund/legal/ops acceptance)
