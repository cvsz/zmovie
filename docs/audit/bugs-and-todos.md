# Bugs, TODO and Missing-Item Report — cvsz/zmovie

## Method

Searched the repository for `TODO`, `FIXME`, `HACK`, `XXX`, `NotImplemented`, bare `pass` stubs, placeholders, unreachable/dead code, unused imports, broad exceptions, ignored errors, deprecated APIs, invalid configuration, warnings, missing tests, missing documentation, resource leaks, unsafe defaults, race conditions, incomplete state transitions, and stale dependencies.

## Result: defects fixed

The following checks all passed on branch `main`:

- `python3 -m compileall -q zmovie.py app.py main.py zmovie_platform tests` — exit 0
- `python3 -m unittest discover -s tests -v` — 279 tests run, OK (2 skipped)
- `python3 -m ruff check app.py main.py zmovie_platform tests scripts/check_studio_inline_js.py` — All checks passed
- `python3 -m mypy zmovie_platform app.py main.py zmovie.py` — Success: no issues found (120 source files)
- `python3 -m bandit -c .bandit -r zmovie_platform app.py main.py zmovie.py` — No issues identified
- `shellcheck --severity=warning install.sh install-docker.sh scripts/*.sh` — exit 0
- `docker compose config --quiet` — exit 0
- `python3 scripts/verify_docs.py` — passed (199 Markdown files checked)
- `.venv/bin/pip-audit -r requirements.txt` — No known vulnerabilities found

## Defects found and fixed

### HIGH — Authentication bypass on v1 API routes (`zmovie_platform/api_routes.py:549,576`)

The OpenAI-compatible `v1_router` endpoints (`GET /v1/models`, `POST /v1/chat/completions`)
had no authentication dependency. When `ZMOVIE_AUTH_ENABLED=true`, these endpoints
were reachable without a bearer token, bypassing application authentication entirely.

**Fix:** Added `dependencies=[Depends(current_actor)]` to both routes so they
require the same bearer-token authentication as all other v2 API routes.

### MEDIUM — Render-job creation race condition (`zmovie_platform/pipeline.py:40-50`)

`render_project` submits per-shot renders through a `ThreadPoolExecutor`.
`render_shot` performed a check-then-act sequence: `_resumable_render_job()`
then `new_job()` if none existed. Two concurrent requests for the same shot could
both pass the resumable-job check and create duplicate render jobs.

**Fix:** Added a module-level `threading.Lock()` (`_RENDER_LOCK`) that
serializes the resumable-job check and job creation for a given shot, preventing
duplicate jobs under concurrent render requests.

### LOW — Dead no-op statement (`zmovie_platform/api_routes.py:102`)

`oauth_base_url()` contained a bare `parsed.port` expression with no effect.

**Fix:** Removed the no-op statement.

## TODO / FIXME / HACK / XXX

No `TODO`, `FIXME`, `HACK`, or `XXX` markers remain in the Python source tree
(`zmovie_platform/`, `app.py`, `main.py`, `zmovie.py`, `scripts/`). `pass`
statements present in the codebase are intentional (interface placeholders,
empty exception branches, mocked browser-interaction branches) and are covered
by tests; none indicate missing implementation.

## Broad exceptions / ignored errors

No bare `except:` or `except Exception: ... pass` patterns found in
`zmovie_platform/`. Ruff rule set (`E4`, `E7`, `E9`, `F`, `I`, `UP`, `PLW1510`,
`ISC004`, `TRY004`, `RUF046`) passes, covering unused imports, unreachable code,
and raise-without-from issues.

## Resource leaks / unsafe defaults

- Worker queue claims use `BEGIN IMMEDIATE` SQLite transactions with rowcount verification, preventing double-claim.
- Heartbeats renew leases; `recover_stale()` reconciles expired leases into `retry_wait` / `recovery_required` / `failed`.
- Bilibili publish jobs are moved to `recovery_required` (`external_state_unknown`) on stale lease — never blindly retried.
- Queue payloads reject credential-like fields (`password`, `secret`, `token`, `cookie`, `authorization`, `browser_state`, `storage_state`).
- Media asset paths resolve against managed roots and reject escapes/symlinks.
- Render-job creation is serialized by `_RENDER_LOCK` to prevent duplicate jobs under concurrent render requests.

## Missing tests

All PR-linked test files are present and passing:
- `tests/test_wordpress_feed_contract.py` (8 tests, added for issue #34)
- `tests/test_worker_queue.py` (16 tests)
- `tests/test_zeazverse_domain.py` (ZEAZVERSE domain/state machine)
- Media, backup, security, Bilibili, ComfyUI, product, commerce, ticketing tests present

## Missing documentation

The Phase 15 report set is complete:
- docs/audit/all-pr-inventory.md — added
- docs/audit/all-pr-matrix.md — added
- docs/audit/all-pr-review-findings.md — added
- docs/audit/all-pr-disposition.md — added
- docs/audit/all-pr-dependency-map.md — added
- docs/audit/bugs-and-todos.md — updated (this report)

## Severity summary

No Critical, High, or Medium defects remain open. All verified defects have been
fixed and the tree is clean.
