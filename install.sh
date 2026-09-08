#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="${ZMOVIE_REPO_URL:-https://github.com/cvsz/zmovie.git}"
BRANCH="${ZMOVIE_BRANCH:-main}"
INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
ENV_DIR="${ZMOVIE_ENV_DIR:-/etc/zmovie}"
ENV_FILE="${ENV_DIR}/zmovie.env"
SERVICE_FILE="/etc/systemd/system/zmovie.service"

log() { printf '\n[zMovie] %s\n' "$*"; }
fail() { printf '\n[zMovie] ERROR: %s\n' "$*" >&2; exit 1; }

if [[ ${EUID} -ne 0 ]]; then
  fail "Run as root (for example: sudo bash install.sh)."
fi

if ! command -v apt-get >/dev/null 2>&1; then
  fail "This installer currently supports Debian/Ubuntu systems with apt-get."
fi

export DEBIAN_FRONTEND=noninteractive
log "Installing operating-system prerequisites"
apt-get update -y
apt-get install -y --no-install-recommends python3 python3-venv python3-pip git curl ca-certificates

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  log "Creating service account: $SERVICE_USER"
  useradd --system --home-dir "$INSTALL_DIR" --create-home --shell /usr/sbin/nologin "$SERVICE_USER"
fi

mkdir -p "$INSTALL_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

if [[ -d "$INSTALL_DIR/.git" ]]; then
  log "Updating existing zMovie checkout"
  runuser -u "$SERVICE_USER" -- git -C "$INSTALL_DIR" fetch --prune origin "$BRANCH"
  runuser -u "$SERVICE_USER" -- git -C "$INSTALL_DIR" checkout "$BRANCH"
  runuser -u "$SERVICE_USER" -- git -C "$INSTALL_DIR" pull --ff-only origin "$BRANCH"
elif [[ -n "$(find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  fail "$INSTALL_DIR is not empty and is not a zMovie git checkout. Set ZMOVIE_INSTALL_DIR to another path."
else
  log "Cloning zMovie"
  runuser -u "$SERVICE_USER" -- git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

log "Creating/updating Python virtual environment"
if [[ ! -x "$INSTALL_DIR/.venv/bin/python" ]]; then
  runuser -u "$SERVICE_USER" -- python3 -m venv "$INSTALL_DIR/.venv"
fi
runuser -u "$SERVICE_USER" -- "$INSTALL_DIR/.venv/bin/python" -m pip install --upgrade pip
runuser -u "$SERVICE_USER" -- "$INSTALL_DIR/.venv/bin/python" -m pip install -r "$INSTALL_DIR/requirements.txt"

mkdir -p "$ENV_DIR" "$INSTALL_DIR/data"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/data"

if [[ ! -f "$ENV_FILE" ]]; then
  log "Creating runtime environment file"
  cat > "$ENV_FILE" <<EOF
ZMOVIE_HOST=0.0.0.0
ZMOVIE_PORT=${ZMOVIE_PORT:-8080}
ZMOVIE_DATA_DIR=$INSTALL_DIR/data
EOF
  chmod 0640 "$ENV_FILE"
  chown root:"$SERVICE_USER" "$ENV_FILE"
else
  log "Preserving existing $ENV_FILE"
fi

if command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
  log "Installing systemd service"
  cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=zMovie Cinematic Prompt Generator
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$INSTALL_DIR/.venv/bin/python $INSTALL_DIR/app.py
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR/data

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable --now zmovie.service
  systemctl restart zmovie.service

  # Read the configured port without executing arbitrary shell content.
  PORT="$(awk -F= '$1=="ZMOVIE_PORT" {print $2}' "$ENV_FILE" | tail -n1 | tr -d '[:space:]')"
  PORT="${PORT:-8080}"

  log "Waiting for health endpoint"
  healthy=0
  for _ in $(seq 1 20); do
    if curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
      healthy=1
      break
    fi
    sleep 1
  done

  if [[ "$healthy" -ne 1 ]]; then
    systemctl --no-pager --full status zmovie.service || true
    journalctl -u zmovie.service -n 50 --no-pager || true
    fail "Service did not become healthy."
  fi

  log "Installation complete"
  printf 'Web UI:  http://<server-ip>:%s/\n' "$PORT"
  printf 'Health:  http://127.0.0.1:%s/api/health\n' "$PORT"
  printf 'Status:  systemctl status zmovie\n'
  printf 'Logs:    journalctl -u zmovie -f\n'
else
  log "systemd is unavailable; installation completed without a persistent service"
  printf 'Start manually with:\n'
  printf '  cd %q && ZMOVIE_HOST=0.0.0.0 ZMOVIE_PORT=%q ZMOVIE_DATA_DIR=%q .venv/bin/python app.py\n' "$INSTALL_DIR" "${ZMOVIE_PORT:-8080}" "$INSTALL_DIR/data"
fi
