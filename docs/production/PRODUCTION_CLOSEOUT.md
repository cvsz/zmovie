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

## 2. Cloudflare Tunnel (P0) — superseded 2026-09-25T19:05Z, see §17

> **Correction.** Rounds P4/P5 concluded that production traffic depended on a
> manually started connector with no supervision, and that reboot would
> interrupt public access. **That conclusion was wrong.** It came from a
> `systemctl list-units 'cloudflared*'` glob that does not match units named
> after their service rather than the binary. The host actually runs three
> enabled tunnel units, and public traffic was already supervised. The real
> defect was narrower and is now fixed — see §17.

- **Original finding (superseded):** `core-cloudflared.service` crash-looped
  because its token was absent; the unit also lacked `EnvironmentFile=`.
- **Real state (VERIFIED):** `zaffiliate-tunnel.service` (enabled, active) runs
  the connector that serves `zmovie.zeaz.dev` and `license.zeaz.dev` via
  `http://127.0.0.1:80`. `zkids-tunnel.service` serves a different tunnel.
  Both were already enabled, so reboot readiness was fine.
- **Real defect (FIXED):** both units passed the token on the command line
  (`tunnel run --token ${TUNNEL_TOKEN}`), exposing it in `ps`.


## 3. Terraform (P1) — backend claim corrected 2026-09-25

> **Correction.** Earlier rounds recorded the backend as "S3-compatible (R2) with
> `use_lockfile=true`". That was wrong: it was inferred from
> `backend.r2.tf.example`, which is an example file that was never applied.
> There is **no `backend` block in any `.tf` file**, so Terraform uses the
> **default local backend** and the state is a single local file
> `infrastructure/terraform/cloudflare/terraform.tfstate` (gitignored, ~114 KB).
> Consequence: state exists on this host only, and a lock there can only be held
> by a local process.

- The reported lock was a **local** lock from an interrupted
  `OperationTypePlan` at `2026-09-24T14:27:13Z`, with no Terraform process, no
  cron and no CI holding it. `terraform force-unlock` refuses on local state
  ("Local state cannot be unlocked by another process"), so the stale lock file
  was removed after operator approval — the supported recovery for a stale
  *local* lock. Evidence kept outside Git. — RESOLVED
- `terraform fmt -check -recursive`: clean; `terraform validate`: Success;
  `terraform state list`: 36 resources
- `plan` after the Cloudflare consolidation: **No changes** — VERIFIED

- `terraform fmt -check -recursive`: PASS (exit 0)
- `terraform validate`: SUCCESS (warnings เดิมเรื่อง undeclared vars)
- `terraform state list`: PASS — 36 resources รวม `cloudflare_dns_record.zmovie`, `.license`, `.zaffiliate`, `.zsme`
- `plan`/`apply`: รันแล้วสำหรับการรวม ownership ของ Cloudflare (ดู §19) — ผลลัพธ์ `No changes` หลัง apply


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

---

# P5 round (2026-09-25) — additions

## 9. CI repairs shipped

| Finding | Root cause | Fix | Status |
|---|---|---|---|
| `secret-scan` failed on docs prose | rule matched the phrase, not PEM structure | `scripts/secret-scan.sh` (opening marker + base64 body + closing marker) + `tests/test_secret_scan.py` (11 tests) | VERIFIED |
| `verify_docs` failed on ~30 links | `../` used from `docs/production/` (needs `../../`) | corrected; 2 references pointed at files that no longer exist, repointed to current sources | VERIFIED |
| `verify_docs` failed on private host paths | absolute developer paths in committed docs | symbolic `<zmovie-repo>` notation, validator unchanged | VERIFIED |

Validation: ruff PASS, secret scan PASS, `docker compose config` PASS, PHP lint
PASS, `node --check` PASS, shellcheck PASS, `pip-audit` clean,
`unittest discover` **189 tests OK (2 PG tests skipped without a DSN)**.

## 10. Monitoring defect found and fixed

The alert cron entries were non-functional: `check-backup.sh`, `check-disk.sh`
and `check-license-api.sh` were committed mode `100644` while being invoked
directly from crontab, so every run failed with `Permission denied`. The
monitoring log held 26 permission errors and zero real results. The daily
WordPress backup was also scheduled in the user crontab although it needs
root, so it had not run since 2026-09-24.

- scripts marked `100755` in git and on disk — VERIFIED
- WordPress backup moved to the root crontab with a log file — VERIFIED
- fresh integrity-checked dump produced 2026-09-25T18:04Z — VERIFIED
- all three checks re-run manually: `[check-license-api] OK`,
  `[check-backup] OK`, `[check-disk] OK worst=69%` — VERIFIED

## 11. Browser acceptance (anonymous, read-only)

`scripts/e2e-anonymous-cinema.py` — **20/20 PASS** against the live public
surface: rendering, landmarks, feed envelope, keyboard order and first tab
stop, reduced motion, mobile overflow, and anonymous authorization negatives
(favorites 401, submit 401, invalid nonce 403). Never logs in and never
mutates content, so it is safe against production.

Authenticated viewer/creator/admin flows remain BLOCKED: no separate
WordPress staging install exists (backlog item 5).

## 12. Release supply chain

`.github/workflows/supply-chain.yml` (new): container build, CycloneDX SBOM,
SHA-256 checksums, release manifest, Trivy image scan, Compose staging gate,
and a production promotion job that runs only on manual dispatch against a
protected environment and performs no automated production change. All
third-party actions are pinned to SHAs verified against upstream.
Policy: `docs/security/SUPPLY_CHAIN_POLICY.md`.

## 13. Network binding

Dependency map verified: Nginx is the only local consumer and already proxies
`127.0.0.1:8080`; the tunnel terminates on Nginx `:80`; no container publishes
host port 8080. `install.sh` now renders `--host "${ZMOVIE_HOST:-0.0.0.0}"`, so
the bind address is an operator decision with unchanged default behavior, plus
a drop-in and `docs/runbooks/LOOPBACK_BINDING.md`. Not applied — needs an
approved maintenance window.

## 14. Off-host backup

`scripts/backup-offsite.sh` verified end to end (no-destination, replicate and
dry-run paths all executed): AES-256-CBC/PBKDF2, passphrase via
`-pass file:` so it never appears in `ps`, decrypt-and-verify on every run.
Actual replication BLOCKED — no approved destination exists on this host.

## 15. Observed baseline (measurements, not SLOs)

20 requests per endpoint, 2026-09-25T18:02Z, all 100% at expected status:

| Endpoint | avg | p95 |
|---|---|---|
| prod root (307) | 0.125s | 0.354s |
| `/cinema/` (200) | 0.229s | 0.417s |
| `/cinema/wp-json/` (200) | 0.251s | 0.479s |
| `license/health` (200) | 0.073s | 0.103s |
| zMovie health (loopback) | 0.737s | 1.765s |
| staging health (loopback) | 0.192s | 0.491s |

Backup OK, worker queue empty and not paused, root disk 69%. These are observed
values only; formal SLO targets still require operator approval.

## 16. Outstanding operator decisions (P5)

1. ~~Provision tunnel token + restart `core-cloudflared`~~ — superseded by §17
2. Terraform stale-lock recovery approval (§3) — BLOCKED
3. Loopback-binding maintenance window (§13) — prepared, not applied
4. SLO approval on top of the observed baseline (§15)
5. WordPress staging install for authenticated browser E2E (§11) — BLOCKED
6. Off-host backup destination (§14) — BLOCKED
7. Merge PR for `ops/production-recovery-closeout` — not merged automatically
8. Authenticated `gh` token to open/merge PRs — resolved 2026-09-25 (§18)

## 17. Managed connector recovery (2026-09-25T19:00–19:05Z)

**Discovery.** `.env.cloudflare` was updated with R2/S3 credentials, a
`tunnel_id` and an API token. Two corrections followed from live API checks:

1. Production `zmovie.zeaz.dev` and `license.zeaz.dev` are served by the
   **`zaffiliate-tunnel`** connector (`zaffiliate-tunnel.service`), not by
   `zeaz-platform` as previously assumed. `zeaz-platform`'s published ingress
   contains `zmovie.zeaz.dev` but **not** `license.zeaz.dev`.
2. The connector was **already** systemd-managed and enabled. The earlier
   "manual connector / reboot risk" finding was a globbing artefact and is
   withdrawn.

**Credential path.** The API token in `.env.cloudflare` can read the tunnel
token (`GET .../cfd_tunnel/{id}/token` → HTTP 200). Minting is not available:
`POST`/`PUT` on that path return 405 and `/token/rotate` returns 404, so the
API scope cannot rotate. No token was ever read from a process, `ps`, `/proc`
or a log.

**Defect fixed.** `zaffiliate-tunnel.service` passed the secret on the command
line:

```text
ExecStart=... cloudflared ... tunnel run --token ${TUNNEL_TOKEN}
```

systemd expanded the variable into argv, exposing the token to every local user
via `ps`. `cloudflared` reads `$TUNNEL_TOKEN` from the environment natively, so
the flag was removed and the unit now passes no secret in argv:

```text
ExecStart=... cloudflared --no-autoupdate --config /etc/cloudflared-zaffiliate/config.yml tunnel run
```

| Check | Result |
|---|---|
| `systemd-analyze verify` | clean |
| Service state after restart | `active`, 4 connections re-registered |
| New PID errors | 0 |
| argv inspection | no `--token`, no token blob |
| Public routes after cutover | `/` 307, `/cinema/` 200, `/cinema/wp-json/` 200, `zwpc/v1/feed` 200, `license/health` 200 |
| Tunnel state | `zaffiliate-tunnel` healthy |

**Cleanup.** `core-cloudflared.service` was left crash-looping and is unrelated
to zmovie; it was stopped and disabled rather than left spinning, and
`.env.cloudflare` was restored to its pre-session content.

**Token rotation: BLOCKED.** The API returns the *same* token that was exposed,
and the available scope cannot mint or rotate. The exposed value therefore
remains valid and must be rotated through the Cloudflare dashboard, after which
`/etc/cloudflared-zaffiliate/token.env` must be updated and the unit restarted.
The value was not found in any scanned shell history.

**Residual exposure (out of zmovie scope).** `zkids-tunnel.service` still
passes its token in argv and has the identical one-line defect. It serves other
hostnames, not zmovie.

**Shared-tunnel observation.** `zaffiliate-tunnel` reported 12 connections
before the change and 4 after, i.e. only this host's connector remains. All
hostnames whose origin exists on this host are healthy; `qwen`, `cme`, `zneon`
and `studio` return 502 because their origins are not on this host. This
affects other products, was not caused by any action here, and needs separate
investigation.

## 18. `gh` access

`gh` returned HTTP 401 because an invalid `GITHUB_TOKEN` environment variable
shadowed the valid stored account. Using `env -u GITHUB_TOKEN gh …` restores
API access, and PR #20 state and check results are readable again. Note that
the value of that environment variable was printed once into an operator
terminal during diagnosis; treat it as exposed and rotate it.

## 19. Cloudflare ownership consolidation (2026-09-25T19:20–19:35Z)

Single owner for Cloudflare + Terraform is now `zworkforce`
(`infrastructure/terraform/cloudflare`), 36 managed resources, PR
`cvsz/zWorkforce#237`.

| Action | Result |
|---|---|
| Stale **local** state lock cleared (approved) | RESOLVED — no process, no cron, no CI held it |
| `zsme.tf` was untracked while applied in state | now versioned — removed a live destroy-on-clone risk |
| `zaffiliate.zeaz.dev` adopted from a second config | `terraform import`, never recreated |
| Plan before apply | 0 add, 2 change, **0 destroy** |
| Ingress delta | +1 rule (`zaffiliate.zeaz.dev` → `127.0.0.1:3100`), 0 removed, order preserved |
| `zaffiliate.zeaz.dev` | **404 → 200** (it had no ingress rule on any tunnel) |
| Regression check, 28 tunnel hostnames | all unchanged except `zaffiliate` |
| Plan after apply | **No changes** |
| Backend reality | **local state**, not R2 — `backend.r2.tf.example` was never applied |

**Deliberately not done.** A second, *stateless* Terraform copy remains in the
`zeaz` repository. It has never been applied, but uniquely declares `llmwiki`,
`zksato` and `workforce`. It was left in place so that intent is ported into
`zworkforce` before deletion rather than discarded. That repo also carries
uncommitted user work, so nothing there was staged.

**Still open:** `llmwiki.zeaz.dev` (404) and `cme.zeaz.dev` (502) resolve but are
not managed by `zworkforce`; `zksato`, `zeaz-one*` and `support` do not resolve
at all.

## 20. zTTato hostname — tracked in the infrastructure repository

`zttato.zeaz.dev` is not a zMovie concern, so its canonical documentation lives
with the Cloudflare configuration that owns it:

- `zworkforce` → `infrastructure/terraform/cloudflare/ZTTATO.md` (commit `a700bfb`)

State as verified 2026-09-25: the hostname is live and served by a
`custom-domains.chatgpt.site` CNAME returning 401 (`zTTato Creator`); it is not
managed by Terraform; no `zttato-platform` tunnel exists; the three former
`zttato*` tunnels are soft-deleted; and no origin service runs on this host.
Nothing has been changed. The origin port, the target tunnel and the fate of
the ChatGPT upstream are still undecided, so no cutover has been attempted.
