#!/usr/bin/env bash
set -Eeuo pipefail

JOB_ID="${1:-}"
INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"

log(){ printf '[zMovie Bilibili preflight] %s\n' "$*"; }
fail(){ printf '[zMovie Bilibili preflight] ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || fail "run as root, for example: sudo bash $0 PUB_JOB_ID"
[[ -n "$JOB_ID" ]] || fail "usage: sudo bash $0 PUB_JOB_ID"
[[ -f "$ENV_FILE" ]] || fail "zMovie environment not found: $ENV_FILE"
[[ -x "$INSTALL_DIR/.venv/bin/python" ]] || fail "zMovie Python not found: $INSTALL_DIR/.venv/bin/python"
id "$SERVICE_USER" >/dev/null 2>&1 || fail "service user not found: $SERVICE_USER"

log "verifying Bilibili-only authenticated browser state"
bash "$INSTALL_DIR/scripts/verify-bilibili-session.sh"

log "verifying approved real publication package and media paths"
runuser -u "$SERVICE_USER" -- bash -lc "
  cd '$INSTALL_DIR'
  set -a
  source '$ENV_FILE'
  set +a
  exec .venv/bin/python -m zmovie_platform.publishers.bilibili_preflight --job '$JOB_ID'
"

log "PASS: Bilibili publication preflight complete"
