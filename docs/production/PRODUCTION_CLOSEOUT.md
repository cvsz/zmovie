# Production Closeout — P4 Execution (2026-09-25)

> บันทึกสถานะหลังจบรอบ P4 (ภาษาไทย) — อ้างเฉพาะสิ่งที่ตรวจสอบจริง
> หลักฐาน sanitized ใน `/tmp/zmovie-p4-evidence-20260925/` (นอก Git)

## 1. Repository states

| Repo | Branch | HEAD | Remote | สถานะ |
|---|---|---|---|---|
| zmovie | main | `35a2e6f` | origin/main `329d821` (ahead 1) | VERIFIED — งานผู้ใช้ต้อง preserve ห้าม reset |
| zworkforce | fix/security-production-secrets | `25a6402` | ตรง remote | VERIFIED |

- zmovie untracked (pre-existing, ไม่แตะ): `deploy/cloudflared/core-cloudflared.service.example`, `docs/ZMOVIE_MASTER_P4-1.md`, `docs/ZMOVIE_MASTER_P4-2.md`, `docs/runbooks/CLOUDFLARED_RECOVERY.md`, `docs/runbooks/POSTGRES_INTEGRATION.md`
- Commits ทั้งหมด GPG-signed (EDDSA `CD57FEA24696DC7E1DB25A8A220A4C8CCC7D2D50`)

## 2. Cloudflare Tunnel (P0)

- **Root cause (VERIFIED):** `core-cloudflared.service` crash-loop (restart counter ~126) เพราะ `CLOUDFLARE_TUNNEL_TOKEN` ไม่มีใน `/home/cvsz/zworkforce/.env.cloudflare` (0600) และ unit ที่ติดตั้งขาด `EnvironmentFile=` (ต่างจาก template)
- **Fix ที่ทำ (IMPLEMENTED):** backup unit ไป `/tmp/core-cloudflared.service.bak-20260925` แล้วเพิ่ม `EnvironmentFile=/home/cvsz/zworkforce/.env.cloudflare` ให้ตรง template, `daemon-reload` ผ่าน, service ยัง `activating` ตามคาด (รอ token) — manual connectors ไม่กระทบ (ยัง 2 processes)
- **Secure delivery (VERIFIED):** wrapper `cloudflare-tunnel.sh` ส่ง token ผ่าน env `TUNNEL_TOKEN` แล้ว `unset` ต้นทาง, `ps` ไม่เห็น secret; `cloudflared 2026.9.1` รองรับ `--token-file` / `$TUNNEL_TOKEN_FILE`
- **Traffic continuity (VERIFIED 2026-09-25 ~17:00 UTC):** `https://zmovie.zeaz.dev/` 307, `/cinema/` 200, `https://license.zeaz.dev/health` 200
- **Token rotation:** BLOCKED — token เดิม visible ใน argv ของ manual connectors ถือว่า potentially compromised ต้อง rotate หลัง cutover (ต้อง operator approval)
- **Reboot readiness:** BLOCKED — unit `enabled` + `Restart=always` แล้ว แต่ยังไม่ healthy จนกว่า token จะมา; ห้าม reboot prod โดยไม่มี approval

**Operator decision:** provision `CLOUDFLARED_TUNNEL_TOKEN` ของ tunnel `zeaz-platform` เดิมลง `.env.cloudflare` (0600) ผ่าน dashboard/scoped token แล้ว `sudo systemctl restart core-cloudflared` ตาม `docs/runbooks/CLOUDFLARED_RECOVERY.md`

## 3. Terraform (P1)

- Backend: S3-compatible (R2) + `use_lockfile=true` — VERIFIED
- Lock: `.terraform.tfstate.lock.info` ค้างจาก `OperationTypePlan` โดย `cvsz@core.zeaz.dev` เมื่อ `2026-09-24T14:27:13Z`; ไม่มี terraform process รันอยู่ (`pgrep -c terraform` = 0) — สันนิษฐาน stale แต่**ห้าม force-unlock** ต้องใช้ backend recovery หลัง operator approval — BLOCKED
- `terraform fmt -check -recursive`: PASS (exit 0)
- `terraform validate`: SUCCESS (warnings เดิมเรื่อง undeclared vars)
- `terraform state list`: PASS — มี `cloudflare_dns_record.zmovie` และ `.license`
- `plan`/`apply`: ไม่รัน (รอ lock resolution + approval) — BLOCKED

## 4. PostgreSQL (P3 ใน P4)

- Isolated container `postgres:18-alpine` loopback `127.0.0.1:15432`, disposable password, synthetic data — VERIFIED
- `tests.test_postgres_readiness`: **4/4 PASS** (ledger idempotency, rollback contract, 6-thread seat-hold ชนะ 1 ราย, pg_dump/pg_restore roundtrip)
- Full suite พร้อม `ZMOVIE_PG_DSN`: **178/178 PASS** (17.3s)
- Container ลบแล้ว (`docker rm -f`) — MySQL `zmovie_cinema` ไม่กระทบ
- Production migration: BLOCKED (ต้องแผนแยก + approval)

## 5. CI / Security toolchain

- PASS: `ruff` (all checks), `verify_docs` (exit 0; notes เรื่อง absolute paths ใน P4 spec เดิม — minimal-diff ไม่แตะ), `docker compose config`, `php -l` ทุกไฟล์, `node --check` 4 ไฟล์, `shellcheck`, `pip-audit` (no known vulns)
- `secret-scan.yml` มีอยู่ครอบคลุม private keys/pattern เดิม — VERIFIED present
- Gaps (PARTIAL/BLOCKED): `pytest` ไม่ติดตั้งใน venv (CI ใช้ unittest), container scan/SBOM/provenance (ไม่มี `syft`/`grype`/`cosign`), release checksums, staging deploy gate, promotion gate — อยู่ใน backlog P2 ข้อ 6

## 6. E2E / Media / Perf / A11y (staging only)

- `zmovie-staging.service` (loopback `:8090`) start + `scripts/deploy-staging.sh`: **deploy verified ที่ `35a2e6f` + CRUD smoke passed** — VERIFIED
- Soak เบา loopback 20 requests: **200 ทั้งหมด, avg ~78ms** (observed, ไม่ใช่ SLO)
- Media pipeline: VERIFIED ผ่าน unit suite (real ffmpeg)
- Authenticated browser E2E (login/favorites/submit/moderation): BLOCKED — ต้อง interactive session
- Screen-reader session: BLOCKED — ต้อง interactive session
- SLO approval + staged soak 7 วัน: pending operator

## 7. Hardening / Backup / Release

- `zmovie.service` bind `0.0.0.0:8080` — UFW `DENY 8080/8000` active (VERIFIED mitigation); Nginx upstream ใช้ `127.0.0.1:8080` แล้วเลยย้ายเป็น loopback ได้ — แต่**ห้าม restart prod** นอก maintenance window ที่ approved — pending
- `scripts/check-backup.sh`: **OK** (re-verified; มี transient FAIL ครั้งเดียวเรื่อง `wp_options` แต่ dump มีตารางครบ 12 tables, re-run ผ่าน)
- SQLite backups `/var/backups/zmovie` มีถึงวันนี้ 03:15 — VERIFIED present
- ห้ามเปิดโดยไม่มี approval: live payments, live ticket sales, public auto-publish, production reboot, destructive Terraform apply, production DB migration

## 8. Outstanding operator decisions

1. Provision tunnel token + restart `core-cloudflared` (§2)
2. Terraform stale-lock recovery approval (§3)
3. Loopback-binding maintenance window (§7)
4. SLO approval + 7-day measurement (§6)
5. Interactive sessions: browser login E2E + screen-reader (§6)
6. Off-host backup copies + at-rest encryption (§7, gap เดิม)
7. PR merge สำหรับ closeout branch นี้ (ไม่ merge เอง)
