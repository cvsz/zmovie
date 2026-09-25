# Feature Matrix — requirements to implementation (2026-09-24, P3 update)

> สถานะตามหลักฐานจริง: VERIFIED = มี check ผ่านตาม scope ที่ระบุ,
> IMPLEMENTED_NOT_VERIFIED = มีโค้ดแต่ยังไม่ผ่าน gate,
> MISSING = ยังไม่มี, BLOCKED = ติด external dependency/approval

## P0 — Critical

| Feature | Status | Location | Evidence |
|---|---|---|---|
| Credential rotation (exposed DB password) | VERIFIED | MariaDB `zmovie_cinema`, `wp-config.php`, `~/.my.cnf`, report redacted | WP connects, no active secret in tracked files, secret-scan CI |
| WordPress REST via `/cinema` prefix | VERIFIED | `deploy/nginx/zmovie-cinema.conf.example`, `/var/www/cinema` symlink | `/cinema/` 200, `/cinema/wp-json/` 200, `zwpc/v1/feed` 200 |
| Cloudflare DNS + tunnel ingress (zmovie + license) | VERIFIED | zworkforce Terraform (`cloudflare_dns_record.zmovie`, `.license`) | `validate` ok, `plan` no changes post-apply, HTTPS 200 ทั้งสอง host |
| License Server + signed-lease integration | VERIFIED | `services/license-server/`, `license.php` contract | 8-case matrix ผ่าน (valid/entitlement/tampered/wrong-key/revoked/expired/missing/422s) + rate limit + WP E2E |
| License HTTPS ingress | VERIFIED | `https://license.zeaz.dev` (Nginx + tunnel, edge-deny admin) | TLS valid, 5/5 consecutive 200, WP `scheme=https` |
| Isolated restore drill | VERIFIED | `docs/production/BACKUP_RESTORE_EVIDENCE.md` | 1s restore, counts + siteurl validated |
| Rollback drill (plugin/theme) | VERIFIED | `docs/production/ROLLBACK_EVIDENCE.md` | backup/extract/boot checks pass |
| Studio→Cinema boundary (no auto-publish) | VERIFIED | `zmovie_platform/studio_cinema.py`, `cinema_import_routes.py` | 7 unit tests (dup/missing/failed/reject/happy-path/token) |
| Backup integrity + failure alerts | VERIFIED (repaired 2026-09-25) | backup script + `scripts/check-backup.sh` + daily cron | พบว่า cron เรียกสคริปต์ mode 644 ทำให้รันไม่ได้จริง 26 ครั้ง; แก้เป็น 100755 + ย้าย WordPress backup ไป root crontab; ทั้ง 3 check รันผ่านจริงแล้ว |
| Baseline suite + docs verification | VERIFIED | manifest venv 163/163, CI-like venv 178/178, `verify_docs` 168 files | `edge_tts`/deps pinned, prompt paths fixed, pip-audit clean; P5: 189 tests OK, secret-scan + docs link/path defects fixed |
| Staging environment | VERIFIED | `/opt/zmovie-staging` worktree + `zmovie-staging.service` + `deploy-staging.sh` | pinned deploys, CRUD smoke, rollback verified, loopback-only |

## P1 — Should fix

| Feature | Status | Blocker / Next |
|---|---|---|
| Commerce sandbox (plans/subs/ledger/webhooks/refunds) | VERIFIED (sandbox) | `zmovie_platform/commerce/` — 9 tests; live PSP BLOCKED (needs approved secret workflow + operator approval) |
| Ticketing API (holds/atomic seats/QR/check-in) | VERIFIED (sandbox) | `zmovie_platform/ticketing/` + `services/cinema-api/` — 7 tests; live sales BLOCKED (payment/refund/legal/ops acceptance) |
| Security audit + privacy export/delete | VERIFIED | `docs/security/THREAT_MODEL.md`, 8 regression tests; full pentest NOT_APPLICABLE this round |
| Probes + smoke + runbooks | VERIFIED | `/livez`, `/readyz`, 6 ops scripts, 3 runbooks; PagerDuty/MTA NOT_APPLICABLE (log-based alerts) |
| Playwright smoke (desktop/mobile/keyboard/feed) | VERIFIED (smoke) | axe 0 violations 3 targets; P5: `scripts/e2e-anonymous-cinema.py` 20/20 บน public surface จริง | browser login/logout + screen-reader pending interactive session |
| docs hygiene (`verify_docs` fully green, secret-scan) | VERIFIED | 168 files pass; literal secrets redacted; workflow self-matches fixed |
| Cinema E2E (login/favorites/submit/moderation/isolation) | VERIFIED (server-side) | 9/9 via FPM probe + full cleanup (0 leftovers); browser login flow pending |
| Membership UI (plans/subs/checkout/cancel/receipts) | VERIFIED (sandbox) | `commerce_routes.py` + `/membership` (Thai/EN, reduced-motion); 7 route tests |
| Media pipeline (upload/FFprobe/transcode/poster) | VERIFIED | `media_pipeline.py` + upload endpoint; 4 tests with real ffmpeg evidence |
| Migration ledger + PG harness | VERIFIED (ledger) | idempotent ledger + rollback-contract tests; live PG BLOCKED (no credentials, will not invent) |

## P2 — Nice to have

| Feature | Status | Blocker / Next |
|---|---|---|
| Media pipeline (transcode/poster/CDN/signed media) | IMPLEMENTED_NOT_VERIFIED | Hooks exist in Studio→Cinema; real-model FFprobe evidence needs operator weights/host |
| Membership lifecycle UI + invoices | IMPLEMENTED_NOT_VERIFIED | Core + API done; WP/member UI MISSING |
| Accessibility audit (WCAG 2.2 AA) | PARTIAL | axe 0 violations (3 targets) + keyboard order verified; screen-reader session pending — do not claim compliance |
| Performance/load SLOs | PARTIAL | Baselines recorded (`A11Y_PERF_EVIDENCE.md`); SLOs PROPOSED, need approval; no disruptive public load tests |
| Staging env + CD pipeline | VERIFIED (staging) | Isolated staging live with deploy/rollback workflow; full CD + image scan pending |
| Container image scan / SBOM signing | IMPLEMENTED_NOT_VERIFIED | `pip-audit` clean + pinned freeze; P5 เพิ่ม `.github/workflows/supply-chain.yml` (CycloneDX SBOM, Trivy scan, checksums, release manifest, promotion gate) + `docs/security/SUPPLY_CHAIN_POLICY.md` | ต้องรันบน hosted CI เพื่อผูก artifact จริง; provenance attestation ยังไม่มี |
| DR snapshots + disk alerts | VERIFIED | `backup-dr.sh` verified manifest, key-restore dry-run (pubkey match), wired crons; P5 เพิ่ม `scripts/backup-offsite.sh` (เข้ารหัส+ตรวจถอดได้จริงทุกครั้ง) | off-host replication BLOCKED: ไม่มี destination ที่อนุมัติแล้วบน host; local staging ไม่ช่วยเรื่อง host loss |
| Live disk pressure | VERIFIED (2026-09-25) | Root 99%→65% (66G free) via Docker builder/image/volume prune + pip/uv/npm/pnpm/journal/apt cleanup; all 25 containers healthy; syslog crash-loop (stale zaffiliate units) stopped+disabled |

## Dependency-ordered backlog (remaining)

1. P0: `CLOUDFLARED_TUNNEL_TOKEN` สำหรับ managed connector (BLOCKED: operator
   ต้อง provision เอง; manual connectors ยังถือ traffic อยู่).
2. P1: Terraform stale-lock recovery approval (BLOCKED: ห้าม force-unlock
   โดยไม่มีอนุมัติ; `validate` ผ่าน, `state list` มี zmovie+license).
3. P1: browser login/logout + screen-reader session (interactive).
4. P1: SLO approval — observed baseline บันทึกแล้ว 2026-09-25 ใน
   `PRODUCTION_CLOSEOUT.md` §15; ยังไม่ใช่ SLO ที่อนุมัติ.
5. P1: off-host backup destination (mechanism VERIFIED, replication BLOCKED).
6. P1: maintenance window เพื่อย้าย bind เป็น loopback (เตรียมไว้แล้ว ยังไม่ apply).
7. ~~P1: disk cleanup (operator-owned data + docker/journals).~~ DONE 2026-09-25 (root 65%, 66G free).
8. P2: WP staging parity (separate WP install) for full browser E2E.
9. P2: provenance attestation + release tagging policy (SBOM/scan/manifest
   ทำแล้วใน `supply-chain.yml`; รอผลรันบน hosted CI).
10. BLOCKED จนกว่าจะ approval: live payments, live ticket sales, public auto-publish,
    live PostgreSQL migration.
    (ห้ามเปิดโดยไม่มี payment/refund/legal/ops acceptance)
