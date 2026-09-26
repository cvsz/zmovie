#!/usr/bin/env bash
# License API availability check (exit non-zero on failure for monitoring).
set -Eeuo pipefail

LICENSE_API="${ZEAZ_LICENSE_API:-http://127.0.0.1:8085}"

fail(){ printf '[check-license-api] FAIL: %s\n' "$*" >&2; exit 1; }
command -v curl >/dev/null 2>&1 || fail "curl is required"

curl -fsS --max-time 8 "$LICENSE_API/health" | grep -q '"healthy"' \
  || fail "license API unhealthy: $LICENSE_API/health"
curl -fsS --max-time 8 "$LICENSE_API/v1/public-key" | grep -q 'public_key' \
  || fail "license public-key endpoint failed"

printf '[check-license-api] OK: %s\n' "$LICENSE_API"
