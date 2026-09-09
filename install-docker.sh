#!/usr/bin/env bash
set -Eeuo pipefail

command -v docker >/dev/null 2>&1 || { echo "[zMovie] Docker is required" >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "[zMovie] Docker Compose v2 is required" >&2; exit 1; }
command -v openssl >/dev/null 2>&1 || { echo "[zMovie] openssl is required" >&2; exit 1; }

ENV_FILE="${ZMOVIE_ENV_FILE:-.env}"
if [[ ! -f "$ENV_FILE" ]]; then
  ADMIN_PASSWORD="${ZMOVIE_ADMIN_PASSWORD:-$(openssl rand -hex 16)}"
  SECRET_KEY="${ZMOVIE_SECRET_KEY:-$(openssl rand -hex 32)}"
  cat >"$ENV_FILE" <<EOF
ZMOVIE_PORT=${ZMOVIE_PORT:-8080}
ZMOVIE_AUTH_ENABLED=true
ZMOVIE_ENABLE_DOCS=${ZMOVIE_ENABLE_DOCS:-false}
ZMOVIE_SECRET_KEY=${SECRET_KEY}
ZMOVIE_ADMIN_USER=${ZMOVIE_ADMIN_USER:-admin}
ZMOVIE_ADMIN_PASSWORD=${ADMIN_PASSWORD}
ZMOVIE_PROVIDER_WEBHOOK=${ZMOVIE_PROVIDER_WEBHOOK:-}
ZMOVIE_PROVIDER_TOKEN=${ZMOVIE_PROVIDER_TOKEN:-}
ZMOVIE_COMFYUI_URL=${ZMOVIE_COMFYUI_URL:-http://host.docker.internal:8188}
ZMOVIE_COMFYUI_WORKFLOW=${ZMOVIE_COMFYUI_WORKFLOW:-/app/workflows/comfyui/workflow_api.json}
ZMOVIE_BILIBILI_STUDIO_URL=https://studio.bilibili.tv/
ZMOVIE_BILIBILI_HEADLESS=true
ZMOVIE_BILIBILI_AUTO_PUBLISH=false
ZMOVIE_BILIBILI_TIMEOUT_MS=120000
EOF
  chmod 0600 "$ENV_FILE"
  echo "[zMovie] Initial admin user: ${ZMOVIE_ADMIN_USER:-admin}"
  echo "[zMovie] Initial admin password: ${ADMIN_PASSWORD}"
  echo "[zMovie] Save this password now."
else
  echo "[zMovie] Reusing existing ${ENV_FILE}; credentials/secrets preserved."
fi

docker compose --env-file "$ENV_FILE" up -d --build
PORT="$(sed -n 's/^ZMOVIE_PORT=//p' "$ENV_FILE" | tail -n 1)"
PORT="${PORT:-8080}"
for _ in $(seq 1 90); do
  if curl -fsS "http://127.0.0.1:${PORT}/api/v2/health" >/dev/null 2>&1; then
    echo "[zMovie] Healthy: http://127.0.0.1:${PORT}/studio"
    echo "[zMovie] Headless Chromium is included in the image."
    echo "[zMovie] Perform the one-time Bilibili Google login on a GUI checkout and securely copy storage_state.json into the zmovie-data volume at /app/data/bilibili/storage_state.json."
    exit 0
  fi
  sleep 1
done

docker compose --env-file "$ENV_FILE" ps
docker compose --env-file "$ENV_FILE" logs --tail 100 zmovie
exit 1
