#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"

log(){ printf '[zMovie Bilibili launch] %s\n' "$*"; }
fail(){ printf '[zMovie Bilibili launch] ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || fail "run as root, for example: sudo bash $0"
[[ -f "$ENV_FILE" ]] || fail "zMovie environment not found: $ENV_FILE"
[[ -x "$INSTALL_DIR/.venv/bin/python" ]] || fail "zMovie Python not found: $INSTALL_DIR/.venv/bin/python"
id "$SERVICE_USER" >/dev/null 2>&1 || fail "service user not found: $SERVICE_USER"
command -v ffmpeg >/dev/null 2>&1 || fail "ffmpeg not found"
command -v ffprobe >/dev/null 2>&1 || fail "ffprobe not found"

log "creating a real managed launch candidate; no Bilibili upload or approval is performed"
runuser -u "$SERVICE_USER" -- bash -lc "
  cd '$INSTALL_DIR'
  set -a
  source '$ENV_FILE'
  set +a
  exec .venv/bin/python -m zmovie_platform.publishers.bilibili_launch_candidate
"

log "candidate created; review it with scripts/list-bilibili-publish-candidates.sh before preparing publication"
