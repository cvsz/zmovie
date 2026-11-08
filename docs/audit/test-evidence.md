# Test Evidence — zMovie Enterprise Audit

**Baseline SHA:** `67023e1a5a4f69f5154ac19c58b5e390154f3d91`  
**Branch:** `feat/zmovie-enterprise-production-hardening`  
**Python:** 3.14.4 (`.venv`)  
**Date:** Sun Nov 08 2026

## Test results

```
Ran 240 tests in 10.405s
OK (skipped=2)
```

- 240 tests run (232 pre-existing + 8 new WordPress feed contract tests).
- 2 skipped (pre-existing skips, unchanged).
- 0 failed.

Test files exercised include: worker queue (13 cases), secret scan (11 cases), WordPress cinema API, ComfyUI provider, Bilibili hardening/preflight/confirmation, production workflow, media pipeline/preview, oauth security, security boundaries/regression, zeazverse domain, zflow, app, platform, product, backup health, runtime ops/paths, and more.

## Quality checks

| Check | Command | Result |
|-------|---------|--------|
| Python compilation | `python -m compileall -q zmovie.py app.py main.py zmovie_platform tests scripts` | exit 0 |
| Ruff lint | `ruff check app.py main.py zmovie_platform tests scripts/...` | exit 0, all passed |
| Documentation validation | `python scripts/verify_docs.py` | exit 0, 186 markdown files |
| Repository audit | `python scripts/validate_repo.py` | AUDIT PASSED (13 checks) |
| Shell syntax | `bash -n install.sh install-docker.sh scripts/*.sh wp-installer/*.sh` | exit 0 |
| JS syntax | `node --check static/*.js` | exit 0 |
| Secret scan | `bash scripts/secret-scan.sh` | exit 0, clean (481 tracked files) |
| Docker compose config | `docker compose config --quiet` | exit 0 |
| Docker build | `docker build -t zmovie:test .` | OK, runtime imports OK |

## Docker health evidence (issue #34)

- Image `zmovie:test` built from current main.
- Container started healthy (`FailingStreak: 0`).
- `GET /api/v2/health` → HTTP 200 `{"status":"ok",...}`.

## New regression tests

`tests/test_wordpress_feed_contract.py` — 8 tests covering populated feed, empty feed, invalid pagination, missing configuration, upstream provider errors, both route aliases, invalid response structure, and credential non-leakage.

## Evidence limitations

The following are **not** covered by this test run because they require external infrastructure, operator-supplied media, or real provider credentials and must not be fabricated:

- Real accelerated video render (ComfyUI/SDCPP with real model weights and GPU).
- ffprobe-validated real media output from a full render pipeline.
- Real Bilibili public publication (`remote_confirmation=true`).
- Real YouTube publishing.
- Cloudflare Tunnel ingress.
- Off-host encrypted backup and restore against production-like data.
