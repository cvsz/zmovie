#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="${ZMOVIE_REPO_URL:-https://github.com/cvsz/zmovie.git}"
REPO_REF="${ZMOVIE_REPO_REF:-main}"
INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
DATA_DIR="${ZMOVIE_DATA_DIR:-/var/lib/zmovie}"
CONFIG_DIR="${ZMOVIE_CONFIG_DIR:-/etc/zmovie}"
ENV_FILE="${CONFIG_DIR}/zmovie.env"
SERVICE_FILE="/etc/systemd/system/zmovie.service"
BACKUP_DIR="${ZMOVIE_BACKUP_DIR:-/var/backups/zmovie}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
PORT="${ZMOVIE_PORT:-8080}"
PUBLIC_BASE_URL="${ZMOVIE_PUBLIC_BASE_URL:-http://zmovie.zeaz.dev}"
ACTION="${1:-install}"
PLAYWRIGHT_DIR="${DATA_DIR}/playwright"
INSTALL_TMP=""

log(){ printf '[zMovie] %s\n' "$*"; }
fail(){ printf '[zMovie] ERROR: %s\n' "$*" >&2; exit 1; }
need_root(){ [[ "${EUID}" -eq 0 ]] || fail "run as root (for example: curl ... | sudo bash)"; }
random_hex(){ openssl rand -hex "${1:-24}"; }
cleanup_install_tmp(){
  if [[ -n "${INSTALL_TMP:-}" ]]; then
    rm -rf -- "$INSTALL_TMP"
    INSTALL_TMP=""
  fi
}
trap cleanup_install_tmp EXIT

backup_data(){
  mkdir -p "$BACKUP_DIR"
  if [[ -f "$DATA_DIR/zmovie.db" ]]; then
    local stamp target
    stamp="$(date -u +%Y%m%dT%H%M%SZ)"
    target="$BACKUP_DIR/zmovie-${stamp}.db"
    python3 - "$DATA_DIR/zmovie.db" "$target" <<'PY'
import sqlite3
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
temp = target.with_suffix(".tmp")
temp.unlink(missing_ok=True)
try:
    with sqlite3.connect(source) as src, sqlite3.connect(temp) as dst:
        src.backup(dst)
    with sqlite3.connect(temp) as check:
        result = check.execute("PRAGMA quick_check").fetchone()
        if result is None or str(result[0]).lower() != "ok":
            raise SystemExit(f"SQLite integrity check failed: {result}")
        violations = check.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise SystemExit(f"SQLite foreign-key check failed: {violations[:10]}")
    temp.replace(target)
finally:
    temp.unlink(missing_ok=True)
PY
    chmod 0640 "$target"
    log "database backup: $target"
  else
    log "no database exists yet; backup skipped"
  fi
}

status(){
  systemctl --no-pager --full status zmovie || true
  if command -v curl >/dev/null 2>&1; then
    local health_port="$PORT"
    if [[ -f "$ENV_FILE" ]]; then
      health_port="$(sed -n 's/^ZMOVIE_PORT=//p' "$ENV_FILE" | tail -n1)"
      health_port="${health_port:-$PORT}"
    fi
    curl -fsS "http://127.0.0.1:${health_port}/api/v2/health" || true
    printf '\n'
  fi
}

uninstall_service(){
  local purge="${2:-}"
  systemctl disable --now zmovie 2>/dev/null || true
  rm -f "$SERVICE_FILE"
  systemctl daemon-reload
  rm -rf "$INSTALL_DIR"
  rm -rf "$CONFIG_DIR"
  if [[ "$purge" == "--purge" ]]; then
    backup_data
    rm -rf "$DATA_DIR"
    log "service, code, config and data removed; backup retained in $BACKUP_DIR"
  else
    log "service/code/config removed; persistent data retained at $DATA_DIR"
  fi
}

install_or_upgrade(){
  export DEBIAN_FRONTEND=noninteractive
  log "installing OS dependencies"
  apt-get update -y
  apt-get install -y --no-install-recommends python3 python3-venv python3-pip git curl ca-certificates ffmpeg openssl rsync espeak-ng

  if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    useradd --system --home "$DATA_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
  fi
  install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 \
    "$DATA_DIR" "$DATA_DIR/media" "$DATA_DIR/exports" "$DATA_DIR/objects" "$DATA_DIR/publish" "$DATA_DIR/bilibili" "$PLAYWRIGHT_DIR" "$BACKUP_DIR"
  install -d -o root -g "$SERVICE_USER" -m 0750 "$CONFIG_DIR"

  if [[ -d "$INSTALL_DIR" ]]; then
    backup_data
  fi

  local tmp
  tmp="$(mktemp -d)"
  INSTALL_TMP="$tmp"
  log "fetching ${REPO_URL} (${REPO_REF})"
  git clone --depth 1 --branch "$REPO_REF" "$REPO_URL" "$tmp/repo"
  install -d -o root -g root -m 0755 "$INSTALL_DIR"
  rsync -a --delete --exclude '.git/' --exclude '.venv/' --exclude 'data/' "$tmp/repo/" "$INSTALL_DIR/"

  python3 -m venv "$INSTALL_DIR/.venv"
  "$INSTALL_DIR/.venv/bin/python" -m pip install --upgrade pip wheel
  "$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

  log "installing Playwright Chromium and required system libraries"
  PLAYWRIGHT_BROWSERS_PATH="$PLAYWRIGHT_DIR" "$INSTALL_DIR/.venv/bin/python" -m playwright install --with-deps chromium

  local generated_password=""
  if [[ ! -f "$ENV_FILE" ]]; then
    generated_password="${ZMOVIE_ADMIN_PASSWORD:-$(random_hex 16)}"
    local secret
    secret="${ZMOVIE_SECRET_KEY:-$(random_hex 32)}"
    cat >"$ENV_FILE" <<EOF
ZMOVIE_HOST=0.0.0.0
ZMOVIE_PORT=${PORT}
ZMOVIE_DB_PATH=${DATA_DIR}/zmovie.db
ZMOVIE_MEDIA_ROOT=${DATA_DIR}/media
ZMOVIE_EXPORT_ROOT=${DATA_DIR}/exports
ZMOVIE_PUBLISH_ROOT=${DATA_DIR}/publish
ZMOVIE_OBJECT_ROOT=${DATA_DIR}/objects
ZMOVIE_AUDIT_PATH=${DATA_DIR}/audit.jsonl
ZMOVIE_AUTH_ENABLED=${ZMOVIE_AUTH_ENABLED:-true}
ZMOVIE_ENABLE_DOCS=${ZMOVIE_ENABLE_DOCS:-false}
ZMOVIE_SECRET_KEY=${secret}
ZMOVIE_ADMIN_USER=${ZMOVIE_ADMIN_USER:-admin}
ZMOVIE_ADMIN_PASSWORD=${generated_password}
ZMOVIE_TOKEN_TTL=${ZMOVIE_TOKEN_TTL:-86400}
ZMOVIE_CORS_ORIGINS=${ZMOVIE_CORS_ORIGINS:-}
ZMOVIE_PROVIDER_WEBHOOK=${ZMOVIE_PROVIDER_WEBHOOK:-}
ZMOVIE_PROVIDER_TOKEN=${ZMOVIE_PROVIDER_TOKEN:-}
ZMOVIE_COMFYUI_URL=${ZMOVIE_COMFYUI_URL:-http://127.0.0.1:8188}
ZMOVIE_COMFYUI_WORKFLOW=${ZMOVIE_COMFYUI_WORKFLOW:-}
ZMOVIE_COMFYUI_TOKEN=${ZMOVIE_COMFYUI_TOKEN:-}
ZMOVIE_COMFYUI_TIMEOUT=${ZMOVIE_COMFYUI_TIMEOUT:-3600}
ZMOVIE_TTS_PROVIDER=${ZMOVIE_TTS_PROVIDER:-edge}
ZMOVIE_TTS_VOICE=${ZMOVIE_TTS_VOICE:-th-TH-PremwadeeNeural}
ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK=${ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK:-false}
ZMOVIE_BILIBILI_STUDIO_URL=https://studio.bilibili.tv/
ZMOVIE_BILIBILI_STATE_PATH=${DATA_DIR}/bilibili/storage_state.json
ZMOVIE_BILIBILI_HEADLESS=true
ZMOVIE_BILIBILI_AUTO_PUBLISH=false
ZMOVIE_BILIBILI_TIMEOUT_MS=120000
PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_DIR}
EOF
    chmod 0640 "$ENV_FILE"
    chown root:"$SERVICE_USER" "$ENV_FILE"
  else
    if [[ -n "${ZMOVIE_PORT:-}" ]]; then
      sed -i -E "s/^ZMOVIE_PORT=.*/ZMOVIE_PORT=${PORT}/" "$ENV_FILE"
    else
      local existing_port
      existing_port="$(sed -n 's/^ZMOVIE_PORT=//p' "$ENV_FILE" | tail -n1)"
      PORT="${existing_port:-$PORT}"
    fi
    grep -q '^ZMOVIE_PUBLISH_ROOT=' "$ENV_FILE" || printf 'ZMOVIE_PUBLISH_ROOT=%s\n' "$DATA_DIR/publish" >>"$ENV_FILE"
    grep -q '^ZMOVIE_ENABLE_DOCS=' "$ENV_FILE" || printf 'ZMOVIE_ENABLE_DOCS=%s\n' "${ZMOVIE_ENABLE_DOCS:-false}" >>"$ENV_FILE"
    grep -q '^ZMOVIE_TTS_PROVIDER=' "$ENV_FILE" || printf 'ZMOVIE_TTS_PROVIDER=edge\n' >>"$ENV_FILE"
    grep -q '^ZMOVIE_TTS_VOICE=' "$ENV_FILE" || printf 'ZMOVIE_TTS_VOICE=th-TH-PremwadeeNeural\n' >>"$ENV_FILE"
    grep -q '^ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK=' "$ENV_FILE" || printf 'ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK=false\n' >>"$ENV_FILE"
    grep -q '^ZMOVIE_BILIBILI_STATE_PATH=' "$ENV_FILE" || printf 'ZMOVIE_BILIBILI_STATE_PATH=%s\n' "$DATA_DIR/bilibili/storage_state.json" >>"$ENV_FILE"
    grep -q '^ZMOVIE_BILIBILI_HEADLESS=' "$ENV_FILE" || printf 'ZMOVIE_BILIBILI_HEADLESS=true\n' >>"$ENV_FILE"
    grep -q '^ZMOVIE_BILIBILI_AUTO_PUBLISH=' "$ENV_FILE" || printf 'ZMOVIE_BILIBILI_AUTO_PUBLISH=false\n' >>"$ENV_FILE"
    grep -q '^PLAYWRIGHT_BROWSERS_PATH=' "$ENV_FILE" || printf 'PLAYWRIGHT_BROWSERS_PATH=%s\n' "$PLAYWRIGHT_DIR" >>"$ENV_FILE"
  fi

  cat >"$SERVICE_FILE" <<EOF
[Unit]
Description=zMovie AI Movie Production Platform
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=/bin/sh -c 'exec ${INSTALL_DIR}/.venv/bin/uvicorn main:app --host 0.0.0.0 --port "\$ZMOVIE_PORT" --workers 1 --proxy-headers'
Restart=on-failure
RestartSec=3
TimeoutStopSec=30
UMask=0027
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectKernelLogs=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
RestrictRealtime=true
CapabilityBoundingSet=
AmbientCapabilities=
ReadWritePaths=${DATA_DIR}

[Install]
WantedBy=multi-user.target
EOF

  chown -R root:root "$INSTALL_DIR"
  chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"
  systemctl daemon-reload
  systemctl enable --now zmovie
  systemctl restart zmovie

  log "waiting for health check"
  local ok=0
  for _ in $(seq 1 45); do
    if curl -fsS "http://127.0.0.1:${PORT}/api/v2/health" >/dev/null 2>&1; then ok=1; break; fi
    sleep 1
  done
  if [[ "$ok" -ne 1 ]]; then
    systemctl --no-pager --full status zmovie || true
    journalctl -u zmovie -n 100 --no-pager || true
    fail "service failed health validation"
  fi

  PUBLIC_BASE_URL="${PUBLIC_BASE_URL%/}"
  log "installation healthy"
  log "Studio: ${PUBLIC_BASE_URL}/studio"
  log "API docs: disabled by default; set ZMOVIE_ENABLE_DOCS=true to expose ${PUBLIC_BASE_URL}/docs"
  log "Bilibili Google login requires a one-time interactive browser session."
  log "On a GUI host/checkout run: python -m zmovie_platform.publishers.bilibili login"
  log "For a server, securely copy the resulting storage_state.json to ${DATA_DIR}/bilibili/storage_state.json and chown ${SERVICE_USER}:${SERVICE_USER}."
  if [[ -n "$generated_password" ]]; then
    log "Initial admin user: ${ZMOVIE_ADMIN_USER:-admin}"
    log "Initial admin password: ${generated_password}"
    log "Save this password now; upgrades preserve it and do not print it again."
  fi
}

need_root
case "$ACTION" in
  install|--install|upgrade|--upgrade) install_or_upgrade ;;
  backup|--backup) backup_data ;;
  status|--status) status ;;
  uninstall|--uninstall) uninstall_service "$@" ;;
  *) fail "unknown action '$ACTION' (use install, upgrade, backup, status, uninstall [--purge])" ;;
esac
