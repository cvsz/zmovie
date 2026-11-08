# Integration Test Report — cv/zMovie — cvsz/zmovie

## Integration evidence gathered

### Docker Compose staging (issue #34 part A)

The full compose stack was built and started:
- `docker compose build` — PASS
- `ZMOVIE_PORT=19080 docker compose up -d --wait --wait-timeout 300` — PASS
- Container `zmovie-zmovie-1`: `Up 5 seconds (healthy)`
- `GET /api/v2/health` → `{"status":"ok","service":"zmovie","database_exists":true,"ffmpeg":true,"ffprobe":true,...}`
- `GET /api/v2/readyz` → `{"status":"ready","users":1}`
- `docker inspect` → `State.Health.Status: healthy`

This satisfies the staging healthcheck requirement. The container binds to internal port 8080; host port 19080 was used because host port 8080 is occupied by an unrelated host process (not part of this repository).

### WordPress feed contract (issue #34 part B)

A live WordPress/PHP runtime is not available in this environment, so the plugin was not executed against a live WordPress instance. Instead:
- `wp-plugins/zwp-cinema/includes/api.php` was inspected and fixed to return the documented envelope `{items, films, has_more, total, page, per_page}` and to register the `/wp-json/zwpc/v1/films` alias sharing the same contract.
- `tests/test_wordpress_feed_contract.py` — 8 tests, all PASS:
  - populated feed exposes `items` and pagination
  - empty feed is valid
  - invalid pagination rejected
  - missing configuration yields deterministic error
  - upstream provider error yields deterministic error (no credential leakage)
  - both route aliases share the contract
  - invalid response structure rejected
  - error never leaks credentials
- No credentials or customer data are asserted in test logs.

### Worker queue recovery (issue #34 / Phase 6)

`tests/test_worker_queue.py` — 16 tests, all PASS, covering:
- enqueue/get/list roundtrip
- atomic claim and heartbeat
- wrong-worker heartbeat rejected
- mark running and complete
- fail retries when attempts remain; fail exhausts attempts immediately
- pause and resume
- queue status shape
- recover stale render lease → retry_wait
- recover stale Bilibili lease → recovery_required (external_state_unknown, no blind retry)
- worker identity nonempty
- sanitize payload rejects secret keys

### Media pipeline

Real FFmpeg render + ffprobe verification passed (see build-lint-test-report.md): H.264 1280x720@24fps, 120 frames, 5.0s, AAC 44.1kHz, MP4 container, probe_score 100, 89,698 bytes.

## Integrations not executed (external credentials required)

The following integrations are implemented and tested with synthetic/mock inputs, but real external publication was NOT performed (no credentials, and platform terms require explicit human approval):

- YouTube: intentionally deferred (docs/YOUTUBE_ROADMAP.md); no real publication attempted.
- Bilibili: browser-session based, fail-closed, explicit `CONFIRM-PUBLISH` gate; no real submission or publication performed. `submitted != published != remotely confirmed`.
- WordPress Cinema: contract tests pass against the plugin envelope; no live WordPress instance exercised.
- ComfyUI / stable-diffusion.cpp: provider contracts implemented; no real model weights available, so no real-model render evidence (documented as pending, not manufactured).
- Cloudflare Tunnel / Nginx: configuration examples present; no public ingress cutover performed.

## Status

All executable integration tests pass. Remaining integrations require operator-supplied credentials, model weights, or explicit external approval and are recorded as pending rather than fabricated.
