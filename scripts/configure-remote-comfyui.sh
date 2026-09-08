#!/usr/bin/env bash
set -Eeuo pipefail

WORKFLOW_SOURCE="${1:-}"
REMOTE_URL="${2:-}"
ZMOVIE_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ENV_FILE="${ZMOVIE_ENV_FILE:-/etc/zmovie/zmovie.env}"

fail(){ printf '[zMovie remote ComfyUI] ERROR: %s\n' "$*" >&2; exit 1; }
log(){ printf '[zMovie remote ComfyUI] %s\n' "$*"; }

[[ "$EUID" -eq 0 ]] || fail "run with sudo"
[[ -n "$WORKFLOW_SOURCE" ]] || fail "workflow path is required: sudo bash scripts/configure-remote-comfyui.sh /real/path/to/video_workflow_api.json http://10.0.0.20:8188"
[[ -n "$REMOTE_URL" ]] || fail "remote ComfyUI URL is required: use the real private GPU host/IP, not the documentation placeholder"

case "$WORKFLOW_SOURCE" in
  /path/to/*|*/path/to/*) fail "replace the example workflow path with the real API-format workflow JSON path on this zMovie host" ;;
esac
case "$REMOTE_URL" in
  *PRIVATE-GPU*|*GPU-HOST*|*GPU-IP*) fail "replace the example GPU hostname/IP with the real private GPU ComfyUI address, for example http://10.0.0.20:8188" ;;
esac

[[ -f "$WORKFLOW_SOURCE" ]] || fail "workflow file not found: $WORKFLOW_SOURCE"
[[ -f "$ENV_FILE" ]] || fail "zMovie env file not found: $ENV_FILE"

python3 - "$REMOTE_URL" <<'PY'
import ipaddress
import os
import sys
from urllib.parse import urlsplit

url = sys.argv[1]
parsed = urlsplit(url)
if parsed.scheme not in {"http", "https"} or not parsed.hostname:
    raise SystemExit("remote URL must be http(s)://host[:port]")
if parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
    raise SystemExit("remote helper requires a non-loopback ComfyUI host")

# Plain HTTP is accepted only for private/link-local/CGNAT IP space unless the
# operator explicitly acknowledges transport risk. Private DNS names cannot be
# classified locally, so use HTTPS or the override for those.
if parsed.scheme == "http":
    safe = False
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        safe = ip.is_private or ip.is_link_local or ip in ipaddress.ip_network("100.64.0.0/10")
    except ValueError:
        safe = False
    if not safe and os.getenv("ZMOVIE_ALLOW_INSECURE_REMOTE_COMFYUI", "").lower() not in {"1", "true", "yes"}:
        raise SystemExit(
            "refusing plain HTTP to a non-private/unknown remote host; use HTTPS, a private IP/VPN, "
            "or set ZMOVIE_ALLOW_INSECURE_REMOTE_COMFYUI=true intentionally"
        )
PY

log "probing remote renderer: ${REMOTE_URL%/}/system_stats"
STATS="$(curl -fsS --max-time 10 "${REMOTE_URL%/}/system_stats")" || fail "remote ComfyUI is unreachable"
printf '%s\n' "$STATS" | python3 -m json.tool >/dev/null

python3 - "$STATS" <<'PY'
import json
import sys
stats = json.loads(sys.argv[1])
devices = stats.get("devices") or []
accelerated = any(str(d.get("type", "")).strip().lower() not in {"", "cpu"} for d in devices if isinstance(d, dict))
if not accelerated:
    raise SystemExit("remote ComfyUI has no accelerator device; refusing to mark it as production video renderer")
print("accelerator devices:")
for device in devices:
    if isinstance(device, dict):
        print(f"  - {device.get('name', 'unknown')} ({device.get('type', 'unknown')})")
PY

log "installing production video workflow and switching zMovie to the remote renderer"
bash "${ZMOVIE_DIR}/scripts/configure-comfyui.sh" "$WORKFLOW_SOURCE" "$REMOTE_URL" video

HEALTH="$(curl -fsS --max-time 8 http://127.0.0.1:8080/api/v2/health)" || fail "zMovie health endpoint unavailable after configuration"
printf '%s\n' "$HEALTH" | python3 -m json.tool

READY="$(printf '%s' "$HEALTH" | python3 -c 'import json,sys; print(str(bool(json.load(sys.stdin).get("production_video_ready"))).lower())')"
[[ "$READY" == "true" ]] || fail "renderer is connected but production_video_ready is false; inspect workflow role, nodes, and device type above"

log "PASS: remote accelerated ComfyUI is configured for production video rendering"
