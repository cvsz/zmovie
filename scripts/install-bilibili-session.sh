#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE="${1:-}"
INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"

log(){ printf '[zMovie Bilibili session] %s\n' "$*"; }
fail(){ printf '[zMovie Bilibili session] ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || fail "run as root, for example: sudo bash $0 /path/to/storage_state.json"
[[ -n "$SOURCE" ]] || fail "usage: sudo bash $0 /path/to/storage_state.json"
[[ -f "$SOURCE" ]] || fail "state file not found: $SOURCE"
[[ -f "$ENV_FILE" ]] || fail "zMovie environment not found: $ENV_FILE"
[[ -x "$INSTALL_DIR/.venv/bin/python" ]] || fail "zMovie Python not found: $INSTALL_DIR/.venv/bin/python"
id "$SERVICE_USER" >/dev/null 2>&1 || fail "service user not found: $SERVICE_USER"

# Detect partial/version-skew deployments before touching the currently working
# production session. The installer depends on the hardened publisher's
# sanitize-state command, so a newer shell script paired with an older Python
# module must fail closed with an actionable upgrade instruction.
HARDENED_HELP="$($INSTALL_DIR/.venv/bin/python -m zmovie_platform.publishers.bilibili_hardened --help 2>&1 || true)"
if ! grep -q 'sanitize-state' <<<"$HARDENED_HELP"; then
  fail "installed zMovie code is revision-skewed: install-bilibili-session.sh requires the hardened sanitize-state command, but the Python module does not provide it. Do not overwrite the currently authenticated session. Run: curl -fsSL https://raw.githubusercontent.com/cvsz/zmovie/main/install.sh | sudo bash -s -- upgrade ; then rerun this command."
fi

TARGET="$(sed -n 's/^ZMOVIE_BILIBILI_STATE_PATH=//p' "$ENV_FILE" | tail -n1)"
TARGET="${TARGET:-/var/lib/zmovie/bilibili/storage_state.json}"
PLAYWRIGHT_DIR="$(sed -n 's/^PLAYWRIGHT_BROWSERS_PATH=//p' "$ENV_FILE" | tail -n1)"

TMP_SCOPED="$(mktemp)"
TMP_OLD="$(mktemp)"
HAD_OLD=0
cleanup(){ rm -f -- "$TMP_SCOPED" "$TMP_OLD"; }
trap cleanup EXIT

log "sanitizing input to Bilibili-only cookies/origins"
"$INSTALL_DIR/.venv/bin/python" -m zmovie_platform.publishers.bilibili_hardened sanitize-state \
  --input "$SOURCE" \
  --output "$TMP_SCOPED" >/dev/null

if [[ -f "$TARGET" ]]; then
  cp -p -- "$TARGET" "$TMP_OLD"
  HAD_OLD=1
fi

install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0700 "$(dirname "$TARGET")"
install -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0600 "$TMP_SCOPED" "$TARGET"

log "probing Creator Center with the installed session"
probe_cmd=(env "ZMOVIE_BILIBILI_STATE_PATH=$TARGET")
if [[ -n "$PLAYWRIGHT_DIR" ]]; then
  probe_cmd+=("PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_DIR")
fi
probe_cmd+=("$INSTALL_DIR/.venv/bin/python" -m zmovie_platform.publishers.bilibili_hardened session --state "$TARGET")

set +e
PROBE="$(runuser -u "$SERVICE_USER" -- "${probe_cmd[@]}" 2>&1)"
STATUS=$?
set -e

if [[ $STATUS -ne 0 ]] || ! printf '%s' "$PROBE" | python3 -c '
import json, sys
try:
    data=json.load(sys.stdin)
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if data.get("configured") and data.get("checked") and data.get("authenticated") else 1)
'; then
  log "live probe failed; restoring previous session state"
  if [[ $HAD_OLD -eq 1 ]]; then
    install -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0600 "$TMP_OLD" "$TARGET"
  else
    rm -f -- "$TARGET"
  fi
  printf '%s\n' "$PROBE" >&2
  exit 2
fi

printf '%s\n' "$PROBE"
log "PASS: Bilibili session installed, least-privilege scoped, and live-authenticated"
log "target: $TARGET"
