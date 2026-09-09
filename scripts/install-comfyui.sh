#!/usr/bin/env bash
set -Eeuo pipefail

COMFYUI_REPO="${COMFYUI_REPO:-https://github.com/Comfy-Org/ComfyUI.git}"
COMFYUI_REF="${COMFYUI_REF:-master}"
COMFYUI_DIR="${COMFYUI_DIR:-/opt/comfyui}"
COMFYUI_DATA="${COMFYUI_DATA:-/var/lib/comfyui}"
COMFYUI_USER="${COMFYUI_USER:-comfyui}"
COMFYUI_PORT="${COMFYUI_PORT:-8188}"
COMFYUI_BACKEND="${COMFYUI_BACKEND:-auto}"
COMFYUI_PYTHON="${COMFYUI_PYTHON:-python3}"
SERVICE_FILE="/etc/systemd/system/comfyui.service"
ZMOVIE_ENV="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"

log(){ printf '[ComfyUI] %s\n' "$*"; }
fail(){ printf '[ComfyUI] ERROR: %s\n' "$*" >&2; exit 1; }
[[ ${EUID} -eq 0 ]] || fail "run as root"

apt-get update -y
apt-get install -y --no-install-recommends \
  git curl ca-certificates rsync python3-venv python3-pip ffmpeg \
  libgl1 libglib2.0-0 libgomp1

command -v "$COMFYUI_PYTHON" >/dev/null 2>&1 || fail "Python executable not found: $COMFYUI_PYTHON"

if ! id "$COMFYUI_USER" >/dev/null 2>&1; then
  useradd --system --home "$COMFYUI_DATA" --shell /usr/sbin/nologin "$COMFYUI_USER"
fi
for group in render video; do
  if getent group "$group" >/dev/null 2>&1; then
    usermod -a -G "$group" "$COMFYUI_USER"
  fi
done

install -d -o root -g root -m 0755 "$COMFYUI_DIR"
install -d -o "$COMFYUI_USER" -g "$COMFYUI_USER" -m 0750 \
  "$COMFYUI_DATA" "$COMFYUI_DATA/models" "$COMFYUI_DATA/input" \
  "$COMFYUI_DATA/output" "$COMFYUI_DATA/temp" "$COMFYUI_DATA/user" \
  "$COMFYUI_DATA/custom_nodes"

tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
log "fetching ${COMFYUI_REPO} (${COMFYUI_REF})"
git clone --depth 1 --branch "$COMFYUI_REF" "$COMFYUI_REPO" "$tmp/repo"
rsync -a --delete --exclude '.git/' --exclude '.venv/' "$tmp/repo/" "$COMFYUI_DIR/"

"$COMFYUI_PYTHON" -m venv "$COMFYUI_DIR/.venv"
"$COMFYUI_DIR/.venv/bin/python" -m pip install --upgrade pip wheel setuptools

backend="$COMFYUI_BACKEND"
if [[ "$backend" == "auto" ]]; then
  if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
    backend="nvidia"
  elif [[ -e /dev/kfd ]] && command -v rocminfo >/dev/null 2>&1; then
    backend="rocm"
  else
    backend="cpu"
  fi
fi

case "$backend" in
  nvidia)
    log "installing PyTorch for NVIDIA CUDA"
    "$COMFYUI_DIR/.venv/bin/pip" install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu130
    runtime_args=""
    ;;
  rocm|amd)
    log "installing PyTorch for AMD ROCm"
    "$COMFYUI_DIR/.venv/bin/pip" install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm7.2
    runtime_args=""
    ;;
  cpu)
    log "installing CPU PyTorch"
    "$COMFYUI_DIR/.venv/bin/pip" install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    runtime_args="--cpu"
    ;;
  *) fail "unsupported COMFYUI_BACKEND=$backend (use auto, nvidia, rocm, or cpu)" ;;
esac

"$COMFYUI_DIR/.venv/bin/pip" install -r "$COMFYUI_DIR/requirements.txt"

cat >"$SERVICE_FILE" <<EOF
[Unit]
Description=ComfyUI local AI renderer
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${COMFYUI_USER}
Group=${COMFYUI_USER}
SupplementaryGroups=render video
WorkingDirectory=${COMFYUI_DIR}
ExecStart=${COMFYUI_DIR}/.venv/bin/python ${COMFYUI_DIR}/main.py --listen 127.0.0.1 --port ${COMFYUI_PORT} --base-directory ${COMFYUI_DATA} ${runtime_args}
Restart=on-failure
RestartSec=5
TimeoutStopSec=45
UMask=0027
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectKernelLogs=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
RestrictRealtime=true
ReadWritePaths=${COMFYUI_DATA}

[Install]
WantedBy=multi-user.target
EOF

# Remove supplementary groups that do not exist on unusual distributions.
existing_groups=""
for group in render video; do
  if getent group "$group" >/dev/null 2>&1; then
    existing_groups="${existing_groups:+$existing_groups }$group"
  fi
done
if [[ -n "$existing_groups" ]]; then
  sed -i "s/^SupplementaryGroups=.*/SupplementaryGroups=${existing_groups}/" "$SERVICE_FILE"
else
  sed -i '/^SupplementaryGroups=/d' "$SERVICE_FILE"
fi

chown -R root:root "$COMFYUI_DIR"
chown -R "$COMFYUI_USER:$COMFYUI_USER" "$COMFYUI_DATA"
systemctl daemon-reload
systemctl enable --now comfyui
systemctl restart comfyui

log "waiting for http://127.0.0.1:${COMFYUI_PORT}/system_stats"
ok=0
for _ in $(seq 1 90); do
  if curl -fsS "http://127.0.0.1:${COMFYUI_PORT}/system_stats" >/dev/null 2>&1; then
    ok=1
    break
  fi
  sleep 2
done
if [[ "$ok" -ne 1 ]]; then
  systemctl --no-pager --full status comfyui || true
  journalctl -u comfyui -n 120 --no-pager || true
  fail "ComfyUI failed health validation"
fi

if [[ -f "$ZMOVIE_ENV" ]]; then
  if grep -q '^ZMOVIE_COMFYUI_URL=' "$ZMOVIE_ENV"; then
    sed -i -E "s#^ZMOVIE_COMFYUI_URL=.*#ZMOVIE_COMFYUI_URL=http://127.0.0.1:${COMFYUI_PORT}#" "$ZMOVIE_ENV"
  else
    printf 'ZMOVIE_COMFYUI_URL=http://127.0.0.1:%s\n' "$COMFYUI_PORT" >>"$ZMOVIE_ENV"
  fi
  systemctl restart zmovie || true
fi

log "healthy"
log "backend: ${backend}"
log "API: http://127.0.0.1:${COMFYUI_PORT}"
log "models: ${COMFYUI_DATA}/models"
log "custom nodes: ${COMFYUI_DATA}/custom_nodes"
log "next: export a ComfyUI workflow in API format, then run /opt/zmovie/scripts/configure-comfyui.sh WORKFLOW_JSON http://127.0.0.1:${COMFYUI_PORT}"
