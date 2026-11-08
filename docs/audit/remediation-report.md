# Remediation Report — zMovie Enterprise Audit

**Baseline SHA:** `67023e1a5a4f69f5154ac19c58b5e390154f3d91`  
**Branch:** `feat/zmovie-enterprise-production-hardening`

## Remediation performed (P0)

### R1 — WordPress feed contract (issue #34, symptom 2)

**Files changed:**
- `wp-plugins/zwp-cinema/includes/api.php`
- `wp-plugins/zwp-cinema/README.md`

**What changed:**
- Feed endpoint now returns the documented envelope `{ items, films (alias), has_more, total, page, per_page }`.
- `items` is the consumable film list; `films` kept as backward-compatible alias.
- Registered secondary route alias `GET /wp-json/zwpc/v1/films` (same callback, same args) — both aliases share the contract.
- Pagination validation kept via REST `validate_callback` (deterministic 400 for invalid page/per_page).
- Error responses use WordPress REST error shape `{ code, message, data }`; no credentials or customer data.

**Tests added:** `tests/test_wordpress_feed_contract.py` (8 tests): populated feed, empty feed, invalid pagination, missing configuration, upstream provider errors, both route aliases, invalid response structure, credential non-leakage.

**Result:** 8/8 pass; full suite 240 pass, 2 skipped, 0 failed.

### R2 — Docker/staging health (issue #34, symptom 1)

**No code change required.** Investigated on current main: `docker build` OK, `docker compose config` OK, container starts healthy (`FailingStreak: 0`), `/api/v2/health` returns HTTP 200. The unhealthy failure reported in issue #34 was on older main SHAs and does not reproduce on current main.

## Not remediated (blocked, requires operator/external action)

- Real-model video render + ffprobe-validated output.
- Real Bilibili public publication (`remote_confirmation=true`).
- Off-host encrypted backup + restore validation.
- Cloudflare Tunnel token.

## Verification

All local CI-equivalent checks pass (tests, ruff, compileall, verify_docs, validate_repo, shellcheck-equivalent bash -n, node --check, secret scan, docker compose config, docker build).

## Release gate

Production promotion remains blocked until exact-head staging checks pass, an immutable image digest is verified, rollback is verified, and an independent review plus release approval is obtained. This audit does not deploy or cut over DNS.
