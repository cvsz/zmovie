# Staging Remediation — GitHub Issue #34

**Issue:** [cvsz/zmovie#34](https://github.com/cvsz/zmovie/issues/34) — "[P1] Restore staging release admission: container health and WordPress feed contract fail"  
**Status:** Investigated against current main (`67023e1`). Remediation applied to the reproducible defect.  
**Production promotion:** Remains blocked until exact-head staging checks pass (not executed by this audit).

## Symptom 1 — Docker Compose container unhealthy

**Reported:** `staging-release-gate` failed after `docker compose up -d --wait --wait-timeout 300`; container `zmovie-zmovie-1` remained unhealthy.

**Investigation on current main:**
- `docker compose config --quiet` passes.
- `docker build -t zmovie:test .` succeeds; runtime imports OK (`fastapi, uvicorn, playwright, httpx`).
- Ran the image as a container with the compose environment. Result: container reported `Up ... (healthy)`, health `FailingStreak: 0`.
- `GET http://127.0.0.1:8080/api/v2/health` returned HTTP 200 with `{"status":"ok","service":"zmovie","database_exists":true,"ffmpeg":true,"ffprobe":true,...}`.
- The healthcheck exercises `/api/v2/health`, which probes DB, ffmpeg/ffprobe, and ComfyUI/SDCPP readiness without failing the container when a renderer is absent (render_ready may be false, but status stays "ok").

**Root cause:** The unhealthy-container failure was observed on older main SHAs (issue references `9df0770`, `85f71dc`, `69e1690`). Current main (`67023e1`, which includes the Dockerfile python 3.15 fix and `scripts/validate_repo.py`) does not reproduce it. No timeout was blindly increased.

**Action taken:** None required for code — verified the container starts healthy on current main. Captured sanitized diagnostic evidence (image build OK, container healthy, health endpoint 200).

**Verification command (re-runnable):**
```bash
docker build -t zmovie:test .
docker run -d --name zmovie-health -p 18081:8080 \
  -e ZMOVIE_HOST=127.0.0.1 \
  -e ZMOVIE_AUTH_ENABLED=true \
  -e ZMOVIE_SECRET_KEY=<32+ char test secret> \
  -e ZMOVIE_ADMIN_USER=admin \
  -e ZMOVIE_ADMIN_PASSWORD=<long random test password> \
  zmovie:test
# wait ~12s, then:
docker ps --filter name=zmovie-health   # expect "(healthy)"
docker inspect zmovie-health --format '{{json .State.Health}}'   # expect Status=healthy, FailingStreak=0
curl -fsS http://127.0.0.1:18081/api/v2/health   # expect HTTP 200 {"status":"ok"}
docker rm -f zmovie-health
```

## Symptom 2 — WordPress feed contract KeyError: items

**Reported:** `wordpress-staging-smoke` failed with `KeyError: 'items'` while checking `/zwpc/v1/feed?page=1` through both WordPress REST route forms.

**Root cause (verified in code):** The ZeaZ Cinema plugin (`wp-plugins/zwp-cinema/includes/api.php`) returned the envelope `{ films, total, page, per_page }`, but the theme (`themes/zwp-cinema/assets/js/reels.js`) consumes `result.items` and `result.has_more`. A consumer reading `result.items` receives `undefined` → `KeyError: items`.

**Fix applied (`api.php`):**
- Feed now returns the documented envelope: `{ items, films (backward-compatible alias), has_more, total, page, per_page }`.
- `items` is the consumable film list; `films` aliases the same content for existing clients.
- Added a second route alias `GET /wp-json/zwpc/v1/films` bound to the same callback, satisfying the "both route aliases" requirement.
- Pagination args are shared between both aliases; invalid `page`/`per_page` are rejected by REST `validate_callback` (deterministic 400).
- Error responses use the standard WordPress REST error shape `{ code, message, data }` and never include credentials or customer data.

**Docs updated:** `wp-plugins/zwp-cinema/README.md` REST API table now documents the `items` envelope and the `/films` alias.

**Regression tests added:** `tests/test_wordpress_feed_contract.py` — 8 tests:
1. Populated feed exposes `items` and pagination.
2. Empty feed is valid (`items: []`, `total: 0`, `has_more: false`).
3. Invalid pagination is rejected.
4. Missing configuration yields a deterministic error schema.
5. Upstream provider errors yield a deterministic error schema (no credential leakage).
6. Both route aliases (`/feed`, `/films`) share the same contract.
7. Invalid response structure is rejected.
8. Error responses never leak credentials.

## Release admission

- Staging health check: passes on current main (container healthy).
- WordPress feed contract: fixed; contract tests pass.
- Production promotion: **not executed**. Depends on exact-head staging + smoke checks passing in CI, an immutable image digest, verified rollback, and an approved release gate. This audit does not perform deployment or DNS cutover.
