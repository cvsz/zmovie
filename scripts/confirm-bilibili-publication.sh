#!/usr/bin/env bash
set -Eeuo pipefail

JOB_ID="${1:-}"
PUBLIC_URL="${2:-}"
INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"

log(){ printf '[zMovie Bilibili confirm] %s\n' "$*"; }
fail(){ printf '[zMovie Bilibili confirm] ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || fail "run as root, for example: sudo bash $0 PUB_JOB_ID https://www.bilibili.tv/video/..."
[[ -n "$JOB_ID" && -n "$PUBLIC_URL" ]] || fail "usage: sudo bash $0 PUB_JOB_ID https://www.bilibili.tv/video/..."
[[ -f "$ENV_FILE" ]] || fail "zMovie environment not found: $ENV_FILE"
[[ -x "$INSTALL_DIR/.venv/bin/python" ]] || fail "zMovie Python not found: $INSTALL_DIR/.venv/bin/python"
id "$SERVICE_USER" >/dev/null 2>&1 || fail "service user not found: $SERVICE_USER"

case "$PUBLIC_URL" in
  https://bilibili.tv/*/video/*|https://bilibili.tv/video/*|https://*.bilibili.tv/*/video/*|https://*.bilibili.tv/video/*) ;;
  *) fail "public URL must be an HTTPS bilibili.tv /video/ URL" ;;
esac

log "probing public video URL and recording remote confirmation"
runuser -u "$SERVICE_USER" -- bash -lc "
  cd '$INSTALL_DIR'
  set -a
  source '$ENV_FILE'
  set +a
  exec .venv/bin/python -m zmovie_platform.publishers.bilibili_confirm \
    --job '$JOB_ID' \
    --url '$PUBLIC_URL'
"

log "PASS: public Bilibili URL confirmed and durable job state updated"
