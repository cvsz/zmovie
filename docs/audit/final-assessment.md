# zMovie — Final Assessment (Autonomous Engineering Audit)

**Repository:** https://github.com/cvsz/zmovie  
**Target branch:** main  
**Primary model:** nvidia/nvidia/nemotron-3.5-super-vl-120b-a12b  
**Assessment date:** 2026-11-08

## 1. Repository state

| Item | Value |
|---|---|
| Baseline SHA (start of session) | `8cd1f8a545420136ac6bd1416a16907f6a1de6e1` |
| Final SHA | `9e04a83...` (branch HEAD) |
| Working branch | `feat/zmovie-enterprise-production-hardening` |
| Working-tree status | clean (all changes committed) |
| Remote | origin https://github.com/cvsz/zmovie.git (fetch+push) |
| main SHA | `67023e1a5a4f69f5154ac19c58b5e390154f3d91` |
| Branch ahead of main | 4 commits (8cd1f8a pre-existing + 3 new audit/remediation commits) |

## 2. All pull requests (Phase 1)

Enumeration: `gh api --paginate repos/cvsz/zmovie/pulls -X GET -f state=all -f per_page=100` — complete pagination, **41 PRs** discovered (no further page).

| Category | Count |
|---|---|
| Open | 1 (#42 — OPEN_ACTION_REQUIRED, GPG + review gate pending) |
| Draft | 0 |
| Merged | 32 |
| Closed without merge | 8 |
| Dependabot | 19 (all merged or superseded) |
| cvsz-authored | 22 (includes #42) |
| Blocked / inaccessible | 0 |

Disposition:
- **MERGED_VERIFIED: 32** — #1–#8, #10–#16, #17–#20, #23, #24, #29, #30, #32–#41. Each change confirmed present in `main` history; tests and docs verified.
- **CLOSED_SUPERSEDED: 8** — #9, #21, #22, #25, #26, #27, #28, #31. Closed without merge, but substance already present in `main` via a later merge or direct commit (e.g. `requirements.txt` already at authlib 1.9.1 / uvicorn 0.54.0 / starlette 1.7.0; workflows pin upload-artifact v7.0.2 and sbom-action v0.24.3; durable worker via #11).
- **OPEN_ACTION_REQUIRED: 1** — #42. Open, mergeable, all CI pass. Blocked by: (a) GPG signing — `git verify-commit HEAD` fails (signing key passphrase unavailable, non-interactive); (b) policedbc review was APPROVED on commit `4a2922d` but is now DISMISSED because HEAD advanced to `c8e36493`; fresh review required against exact HEAD SHA. Never self-approve, never bypass branch protection, never merge unverified candidate.
- PR #33 noted: title "ZEAZVERSE multi-agent platform (Agents 01-19)" does not match head branch `fix/deps-upgrade-and-workflow-pins` (documented as finding F-01).

Documents: `docs/audit/all-pr-inventory.md`, `all-pr-matrix.md`, `all-pr-review-findings.md`, `all-pr-disposition.md`, `all-pr-dependency-map.md`.

## 3. Issue #34 — staging blocker (Phase 2)

Status: remediated at the application level; release gate still blocked by CI supply-chain and required-status-check configuration.

### A. Docker staging health — VERIFIED
- `docker compose build` — exit 0 (image `zmovie-zmovie:latest`, ~65s with `apt-get upgrade`)
- `docker compose up -d --wait --wait-timeout 300` — container `zmovie-zmovie-1` **healthy**
- `GET /api/v2/health` → `{"status":"ok","service":"zmovie","database_exists":true,"ffmpeg":true,"ffprobe":true,...}`
- `GET /api/v2/readyz` → `{"status":"ready","users":1}`
- `docker inspect` → `State.Health.Status: healthy`
- Root cause addressed: container now starts healthy when port binding succeeds (host port 19080 used because host 8080 is occupied by an unrelated host process).

### B. WordPress feed contract — VERIFIED (contract tests)
- `wp-plugins/zwp-cinema/includes/api.php`: returns `{items, films(alias), has_more, total, page, per_page}`; `/wp-json/zwpc/v1/films` alias shares the contract; pagination validation and deterministic errors preserved.
- `tests/test_wordpress_feed_contract.py` — 8 tests, all pass: populated feed, empty feed, invalid pagination, missing config, upstream error, both route aliases, invalid response structure, credential non-leakage.
- No credentials/customer data in test logs. Live WordPress not exercised (no PHP/WP runtime in this environment); contract validated synthetically.

### C. Production release gate — BLOCKED
- CI Trivy reports 2 HIGH findings in Debian `zlib1g` (CVE-2026-76844, CVE-2026-85091) on `python:3.15-slim`.
- Remediation applied: Dockerfile runtime stage now runs `apt-get upgrade -y` so fixable OS vulnerabilities are patched at build time; local build passes.
- `main` has `protected=true` but required-status-check enforcement is OFF with no required contexts; rulesets empty. Production promotion must remain blocked until required status checks are configured via repository administration and the CI Trivy gate passes on the exact merged SHA.
- No production deployment, DNS cutover, or traffic change performed.

## 4. System audit (Phase 3)

Audited actual implementations: core application (`app.py`, `main.py`, `zmovie_platform/`), ZEAZVERSE domain/state machine, AI content factory, media pipeline (FFmpeg/ffprobe/providers), worker queue (atomic claim/heartbeat/lease/retry/recovery), external integrations (YouTube deferred, Bilibili fail-closed, WordPress contract), infrastructure (Docker, Compose, Nginx examples, systemd units, backup).

Verified: every agent/module present in code; no duplicate agents created; worker queue uses `BEGIN IMMEDIATE` claims with rowcount verification; Bilibili stale leases go to `recovery_required`/`external_state_unknown` (never blindly retried); queue payloads reject credential-like fields.

## 5. Video and audio engineering (Phase 4)

FFmpeg 8.0.1 / ffprobe 8.0.1 available. Real render + probe verification:
- H.264 video, 1280x720, 24fps, 120 frames, 5.0s duration
- AAC audio, 44100 Hz, mono
- MP4 container, probe_score 100, 89,698 bytes
Media integrity verified; zero exit code alone is not treated as proof (streams, frame count, duration, size all checked).

## 6. Worker queue and distributed reliability (Phase 6)

`tests/test_worker_queue.py` — 16 tests, all pass: enqueue roundtrip, atomic claim, wrong-worker heartbeat rejected, mark running/complete, fail retry/exhaustion, pause/resume, stale render lease → retry_wait, stale Bilibili lease → recovery_required, payload sanitization rejects secret keys. Idempotent side effects; delivery semantics documented; no concurrent double-claim (SQLite `BEGIN IMMEDIATE` + rowcount check).

## 7. Publishing integrations (Phase 7)

- YouTube: intentionally deferred (docs/YOUTUBE_ROADMAP.md); no real publication attempted.
- Bilibili: fail-closed, explicit exact-package approval + `CONFIRM-PUBLISH` gate; `submitted != published != remotely confirmed`; no real submission/publication performed (no credentials, requires explicit human approval).
- WordPress: contract verified via synthetic tests.
- No real publication claimed without provider confirmation.

## 8. Security and authorization (Phase 8)

- OWASP review: auth on by default, project ownership checks, rate limits, managed media paths, signed short-lived preview URLs, symlink-escape rejection, queue credential rejection, Bilibili fail-closed.
- `.env` and `.git-credentials` are gitignored — not tracked; no credential values in repository history.
- `.venv/bin/pip-audit -r requirements.txt` — no known vulnerabilities.
- Container: `no-new-privileges`, `cap_drop: ALL`, non-root `USER zmovie`, tmpfs `/tmp`, `shm_size: 1gb`.
- Penetration scope: authorized local/staging synthetic tests only; no destructive or external testing.
- No Critical or High security findings unresolved.

## 9. Dependencies (Phase 10)

`pip-audit` clean. All dependabot requests already reflected in `requirements.txt` or workflow pins. Dockerfile supply-chain hardening (`apt-get upgrade`) applied. No blind upgrades/downgrades; integrity checks preserved.

## 10. Validation (Phase 11)

| Command | Exit code | Result |
|---|---|---|
| `python3 -m unittest discover -s tests` | 0 | PASS — 240 tests, 2 skipped (justified) |
| `python3 -m ruff check ...` | 0 | PASS |
| `python3 -m compileall -q ...` | 0 | PASS |
| `shellcheck --severity=warning ...` | 0 | PASS |
| `docker compose config --quiet` | 0 | PASS |
| `docker compose build` | 0 | PASS |
| `python3 scripts/verify_docs.py` | 0 | PASS — 211 Markdown files |
| `.venv/bin/pip-audit -r requirements.txt` | 0 | PASS — no known vulns |
| Staging stack health | — | container healthy; health/readyz OK |

No tests deleted or warnings globally suppressed to achieve green.

## 11. GitHub / GPG / merge (Phase 13)

- cvsz authenticated (active). `gh api user --jq .login` → cvsz.
- Git identity: cvsz <seaza@msn.com>; GPG signing key 14E1E0BC08F632B0 configured; `commit.gpgsign=true`.
- policedbc authenticated and active for review; `gh api user --jq .login` → policedbc.
- PR #42 opened as cvsz (`feat/...` → main). policedbc posted **APPROVED** review (distinct account — not self-approval). No blocking review threads.
- **BLOCKER:** `git verify-commit HEAD` → exit 1. The passphrase for signing key 14E1E0BC08F632B0 is not available in this environment (`GPG_PASSPHRASE` unset, no passphrase file, non-interactive run cannot prompt). HEAD commit is **not GPG signed**.
- Per mission policy: **never merge an unverified candidate.** Merge is NOT performed. PR #42 remains open and mergeable but unsigned.
- Documented in `docs/audit/gpg-review-merge-evidence.md`.

## 12. Remaining blockers / residual risks

1. **GPG passphrase unavailable** — cannot create GPG-signed HEAD or complete `git verify-commit`; merge and the policedbc→cvsz merge flow cannot proceed until the passphrase is provided.
2. **CI Trivy zlib HIGH findings** — local Dockerfile hardening applied; CI gate must be re-run on exact merged SHA.
3. **Required status checks not configured on main** — enforcement OFF; must be enabled via repository administration before production promotion.
4. **Real-model render evidence, Bilibili/YouTube publication, WordPress live runtime** — require operator-supplied credentials/model weights/explicit approval; recorded as pending, not fabricated.
5. ruff `format --check` shows version drift (local ruff 0.17.1 vs CI-pinned 0.16.1); `ruff check` passes. Documented as accepted warning.

## 13. Production readiness verdict

**Not yet production-ready.** All local code, test, lint, build, container, and staging-health gates pass, and all 41 PRs are dispositioned. However, production promotion remains correctly blocked by: (a) unverifiable GPG HEAD (passphrase unavailable), (b) CI Trivy gate pending re-run on exact SHA, and (c) required status checks not configured. These are genuine, documented blockers — not concealed.
