#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"

log(){ printf '[zMovie Bilibili verify] %s\n' "$*"; }
fail(){ printf '[zMovie Bilibili verify] ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || fail "run as root, for example: sudo bash $0"
[[ -d "$INSTALL_DIR/zmovie_platform" ]] || fail "zMovie package directory not found: $INSTALL_DIR/zmovie_platform"
[[ -f "$ENV_FILE" ]] || fail "zMovie environment not found: $ENV_FILE"
[[ -x "$INSTALL_DIR/.venv/bin/python" ]] || fail "zMovie Python not found: $INSTALL_DIR/.venv/bin/python"
id "$SERVICE_USER" >/dev/null 2>&1 || fail "service user not found: $SERVICE_USER"

TARGET="$(sed -n 's/^ZMOVIE_BILIBILI_STATE_PATH=//p' "$ENV_FILE" | tail -n1)"
TARGET="${TARGET:-/var/lib/zmovie/bilibili/storage_state.json}"
PLAYWRIGHT_DIR="$(sed -n 's/^PLAYWRIGHT_BROWSERS_PATH=//p' "$ENV_FILE" | tail -n1)"
[[ -f "$TARGET" ]] || fail "Bilibili state file not found: $TARGET"

OWNER="$(stat -c '%U' "$TARGET")"
MODE="$(stat -c '%a' "$TARGET")"
[[ "$OWNER" == "$SERVICE_USER" ]] || fail "Bilibili state must be owned by $SERVICE_USER (current owner: $OWNER); run: chown $SERVICE_USER:$SERVICE_USER '$TARGET'"
MODE_DEC=$((8#$MODE))
(( (MODE_DEC & 077) == 0 )) || fail "Bilibili state permissions are too broad ($MODE); run: chmod 600 '$TARGET'"

log "checking browser-state scope without printing cookie values"
SCOPE="$(python3 - "$TARGET" <<'PY'
import json, sys
from urllib.parse import urlparse
from pathlib import Path

p = Path(sys.argv[1])
data = json.loads(p.read_text(encoding='utf-8'))
allowed = ('bilibili.tv', 'bilibili.com')

def ok_host(value):
    host = str(value or '').strip().lower().lstrip('.')
    return any(host == suffix or host.endswith('.' + suffix) for suffix in allowed)

cookies = list(data.get('cookies') or [])
origins = list(data.get('origins') or [])
bad_cookie_domains = sorted({str(c.get('domain') or '') for c in cookies if isinstance(c, dict) and not ok_host(c.get('domain'))})
bad_origins = sorted({str(o.get('origin') or '') for o in origins if isinstance(o, dict) and not ok_host(urlparse(str(o.get('origin') or '')).hostname)})
result = {
    'scope': 'bilibili_only' if not bad_cookie_domains and not bad_origins else 'mixed',
    'cookies': len(cookies),
    'origins': len(origins),
    'unexpected_cookie_domains': bad_cookie_domains,
    'unexpected_origins': bad_origins,
}
print(json.dumps(result, ensure_ascii=False))
if bad_cookie_domains or bad_origins:
    raise SystemExit(2)
PY
)" || {
  printf '%s\n' "$SCOPE"
  fail "browser state contains non-Bilibili scope"
}
printf '%s\n' "$SCOPE"

log "probing Creator Center as the production runtime user"
runtime_cmd=(env "ZMOVIE_BILIBILI_STATE_PATH=$TARGET")
if [[ -n "$PLAYWRIGHT_DIR" ]]; then
  runtime_cmd+=("PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_DIR")
fi
runtime_cmd+=(
  bash -c 'cd "$1"; shift; exec "$@"'
  bash
  "$INSTALL_DIR"
  "$INSTALL_DIR/.venv/bin/python"
  -m zmovie_platform.publishers.bilibili_hardened session --state "$TARGET"
)

PROBE="$(runuser -u "$SERVICE_USER" -- "${runtime_cmd[@]}")"
printf '%s\n' "$PROBE"
printf '%s' "$PROBE" | python3 -c '
import json, sys
data=json.load(sys.stdin)
raise SystemExit(0 if data.get("configured") and data.get("checked") and data.get("authenticated") else 1)
' || fail "live Creator Center session probe failed"

log "PASS: Bilibili-only state scope and live authenticated Creator Center session verified"
