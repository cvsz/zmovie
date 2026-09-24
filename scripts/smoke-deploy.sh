#!/usr/bin/env bash
# Deployment smoke test: health, readiness, public routes (no secrets).
set -Eeuo pipefail

ZMOVIE_URL="${ZMOVIE_URL:-http://127.0.0.1:8080}"

log(){ printf '[smoke-deploy] %s\n' "$*"; }
fail(){ printf '[smoke-deploy] FAIL: %s\n' "$*" >&2; exit 1; }

command -v curl >/dev/null 2>&1 || fail "curl is required"
command -v python3 >/dev/null 2>&1 || fail "python3 is required"

log "GET /api/v2/health"
curl -fsS --max-time 10 "${ZMOVIE_URL%/}/api/v2/health" | python3 -m json.tool >/dev/null \
  || fail "health endpoint failed"

log "GET /api/v2/livez"
curl -fsS --max-time 10 "${ZMOVIE_URL%/}/api/v2/livez" | grep -q '"alive"' \
  || fail "livez failed"

log "GET /api/v2/readyz"
curl -fsS --max-time 15 "${ZMOVIE_URL%/}/api/v2/readyz" | grep -q '"ready"' \
  || fail "readyz failed (DB/migrations not ready)"

log "GET /api/v2/capabilities"
curl -fsS --max-time 10 "${ZMOVIE_URL%/}/api/v2/capabilities" | python3 -m json.tool >/dev/null \
  || fail "capabilities endpoint failed"

log "smoke-deploy passed"
