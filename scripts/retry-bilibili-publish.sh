#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
JOB_ID="${1:-}"
CONFIRM="${2:-}"

log(){ printf '[zMovie Bilibili retry] %s\n' "$*"; }
fail(){ printf '[zMovie Bilibili retry] ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || fail "run as root: sudo bash $0 pub_... CONFIRM-PUBLISH"
[[ "$JOB_ID" =~ ^pub_[A-Za-z0-9]+$ ]] || fail "first argument must be a safe publish job id"
[[ "$CONFIRM" == "CONFIRM-PUBLISH" ]] || fail "external publication requires explicit second argument: CONFIRM-PUBLISH"
[[ -d "$INSTALL_DIR" ]] || fail "install directory not found: $INSTALL_DIR"
[[ -f "$ENV_FILE" ]] || fail "environment file not found: $ENV_FILE"
[[ -x "$INSTALL_DIR/.venv/bin/python" ]] || fail "Python runtime not found"
[[ -f "$INSTALL_DIR/zmovie_platform/publishers/bilibili_ui_compat.py" ]] || fail "UI compatibility publisher not installed; upgrade zMovie first"
[[ -f "$INSTALL_DIR/scripts/preflight-bilibili-publish.sh" ]] || fail "preflight script not installed"
id "$SERVICE_USER" >/dev/null 2>&1 || fail "service user not found: $SERVICE_USER"

STATUS_FILE="$(mktemp)"
cleanup(){ rm -f "$STATUS_FILE"; }
trap cleanup EXIT

status_cmd="cd '$INSTALL_DIR'; set -a; source '$ENV_FILE'; set +a; exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened status --job '$JOB_ID'"
runuser -u "$SERVICE_USER" -- bash -lc "$status_cmd" >"$STATUS_FILE"

STATUS="$(python3 - "$STATUS_FILE" <<'PY'
import json, sys
from pathlib import Path
obj=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(str(obj.get('status') or ''))
PY
)"

case "$STATUS" in
  failed)
    log "job is failed from the prior UI-selector attempt; recording a fresh approval before retry"
    runuser -u "$SERVICE_USER" -- bash -lc "cd '$INSTALL_DIR'; set -a; source '$ENV_FILE'; set +a; exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened approve --job '$JOB_ID'"
    ;;
  approved)
    log "job is already approved"
    ;;
  submitted|published|scheduled)
    fail "refusing duplicate external submission from status: $STATUS"
    ;;
  *)
    fail "job must be failed or approved before retry; current status: ${STATUS:-unknown}"
    ;;
esac

log "running fail-closed preflight"
bash "$INSTALL_DIR/scripts/preflight-bilibili-publish.sh" "$JOB_ID"

log "starting one external retry with delayed metadata-field compatibility"
runuser -u "$SERVICE_USER" -- bash -lc "cd '$INSTALL_DIR'; set -a; source '$ENV_FILE'; set +a; exec .venv/bin/python -m zmovie_platform.publishers.bilibili_ui_compat publish --job '$JOB_ID'"

log "final local job status"
runuser -u "$SERVICE_USER" -- bash -lc "$status_cmd"
