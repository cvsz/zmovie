#!/usr/bin/env bash
set -Eeuo pipefail

ZMOVIE_URL="${ZMOVIE_URL:-http://127.0.0.1:8080}"
COMFYUI_URL="${ZMOVIE_COMFYUI_URL:-http://127.0.0.1:8188}"

log(){ printf '[zMovie doctor] %s\n' "$*"; }
warn(){ printf '[zMovie doctor] WARN: %s\n' "$*" >&2; }
fail(){ printf '[zMovie doctor] FAIL: %s\n' "$*" >&2; exit 1; }

command -v curl >/dev/null 2>&1 || fail "curl is required"
command -v python3 >/dev/null 2>&1 || fail "python3 is required"

log "probing zMovie: ${ZMOVIE_URL%/}/api/v2/health"
ZHEALTH="$(curl -fsS --max-time 8 "${ZMOVIE_URL%/}/api/v2/health")" || fail "zMovie health endpoint is unavailable"
printf '%s\n' "$ZHEALTH" | python3 -m json.tool

COMFYUI_URL="$(printf '%s' "$ZHEALTH" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("comfyui",{}).get("url") or "http://127.0.0.1:8188")')"
log "probing ComfyUI: ${COMFYUI_URL%/}/system_stats"
CSTATS="$(curl -fsS --max-time 8 "${COMFYUI_URL%/}/system_stats")" || fail "ComfyUI API is unavailable"

python3 - "$ZHEALTH" "$CSTATS" <<'PY'
import json
import sys

health = json.loads(sys.argv[1])
stats = json.loads(sys.argv[2])
comfy = health.get("comfyui", {})
system = stats.get("system", {})
devices = stats.get("devices", []) or []

def yes(v):
    return "YES" if bool(v) else "NO"

print("\n=== zMovie Production Doctor ===")
print(f"service_status         : {health.get('status', 'unknown')}")
print(f"ffmpeg                : {yes(health.get('ffmpeg'))}")
print(f"ffprobe               : {yes(health.get('ffprobe'))}")
print(f"comfyui_reachable      : {yes(comfy.get('reachable'))}")
print(f"workflow_configured    : {yes(comfy.get('configured'))}")
print(f"workflow_role          : {comfy.get('workflow_role', 'generic')}")
print(f"workflow_valid         : {yes(comfy.get('workflow_valid'))}")
print(f"nodes_available        : {yes(comfy.get('nodes_available'))}")
print(f"accelerated            : {yes(comfy.get('accelerated'))}")
print(f"render_ready           : {yes(health.get('render_ready'))}")
print(f"production_video_ready : {yes(health.get('production_video_ready'))}")
print(f"comfyui_version        : {system.get('comfyui_version', comfy.get('version', 'unknown'))}")
print(f"python_version         : {system.get('python_version', comfy.get('python_version', 'unknown'))}")
print(f"pytorch_version        : {system.get('pytorch_version', comfy.get('pytorch_version', 'unknown'))}")

print("devices:")
for device in devices:
    print(f"  - {device.get('name', 'unknown')} ({device.get('type', 'unknown')})")

if health.get("production_video_ready"):
    print("\nPROFILE: PRODUCTION_VIDEO_RENDER_HOST")
    print("Next: run a real short-shot video render and record the resulting evidence.")
elif comfy.get("accelerated"):
    print("\nPROFILE: ACCELERATED_RENDER_HOST")
    print("Renderer acceleration is available, but a workflow explicitly classified as role=video is still required.")
else:
    print("\nPROFILE: CPU_ONLY_RENDER_HOST")
    print("Local ComfyUI API integration is valid, but large diffusion-video models are not recommended on this host.")
    print("Recommended production path: keep zMovie here and point ZMOVIE_COMFYUI_URL at a private GPU ComfyUI host.")
    print("Use scripts/configure-remote-comfyui.sh with a production video workflow when that host is available.")

missing = comfy.get("missing_node_types") or []
if missing:
    print("\nMISSING NODE TYPES:")
    for node in missing:
        print(f"  - {node}")
    sys.exit(2)

if not health.get("render_ready"):
    err = comfy.get("error")
    if err:
        print(f"\nNOT READY: {err}")
    sys.exit(3)
PY

log "doctor completed"
