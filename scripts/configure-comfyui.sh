#!/usr/bin/env bash
set -Eeuo pipefail

WORKFLOW_SOURCE="${1:-}"
COMFYUI_URL="${2:-http://127.0.0.1:8188}"
DATA_DIR="${ZMOVIE_DATA_DIR:-/var/lib/zmovie}"
ENV_FILE="${ZMOVIE_ENV_FILE:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
TARGET_DIR="${DATA_DIR}/workflows/comfyui"
TARGET_WORKFLOW="${TARGET_DIR}/workflow_api.json"

fail(){ printf '[zMovie] ERROR: %s\n' "$*" >&2; exit 1; }
log(){ printf '[zMovie] %s\n' "$*"; }
[[ "$EUID" -eq 0 ]] || fail "run with sudo"
[[ -n "$WORKFLOW_SOURCE" ]] || fail "usage: sudo bash scripts/configure-comfyui.sh /path/to/workflow_api.json [http://127.0.0.1:8188]"
[[ -f "$WORKFLOW_SOURCE" ]] || fail "workflow file not found: $WORKFLOW_SOURCE"
[[ -f "$ENV_FILE" ]] || fail "zMovie env file not found: $ENV_FILE"

python3 - "$WORKFLOW_SOURCE" <<'PY'
import json
import sys
from pathlib import Path
path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception as exc:
    raise SystemExit(f"invalid workflow JSON: {exc}")
if not isinstance(payload, dict) or not payload:
    raise SystemExit("workflow must be a non-empty ComfyUI API-format JSON object")
missing = [node_id for node_id, node in payload.items() if not isinstance(node, dict) or "inputs" not in node]
if missing:
    raise SystemExit(f"workflow does not look like API format; invalid nodes: {missing[:10]}")
print(f"validated {len(payload)} workflow nodes")
PY

install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 "$TARGET_DIR"
install -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0640 "$WORKFLOW_SOURCE" "$TARGET_WORKFLOW"

upsert_env(){
  local key="$1" value="$2"
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i -E "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    printf '%s=%s\n' "$key" "$value" >>"$ENV_FILE"
  fi
}

upsert_env ZMOVIE_COMFYUI_URL "$COMFYUI_URL"
upsert_env ZMOVIE_COMFYUI_WORKFLOW "$TARGET_WORKFLOW"
chmod 0640 "$ENV_FILE"
chown root:"$SERVICE_USER" "$ENV_FILE"

log "probing ComfyUI: $COMFYUI_URL"
curl -fsS --max-time 5 "${COMFYUI_URL%/}/system_stats" >/dev/null || fail "ComfyUI is not reachable at $COMFYUI_URL"

systemctl restart zmovie
for _ in $(seq 1 30); do
  if health="$(curl -fsS --max-time 5 http://127.0.0.1:8080/api/v2/health 2>/dev/null)"; then
    printf '%s\n' "$health" | python3 -m json.tool
    ready="$(printf '%s' "$health" | python3 -c 'import json,sys; print(str(bool(json.load(sys.stdin).get("comfyui",{}).get("ready"))).lower())')"
    if [[ "$ready" == "true" ]]; then
      log "ComfyUI is configured and zMovie reports render readiness."
      exit 0
    fi
    fail "zMovie is healthy but ComfyUI readiness failed; inspect comfyui.error and missing_node_types above"
  fi
  sleep 1
done

journalctl -u zmovie -n 80 --no-pager || true
fail "zMovie did not become healthy after ComfyUI configuration"
