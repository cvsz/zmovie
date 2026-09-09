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

CSTATS="{}"
log "probing optional ComfyUI: ${COMFYUI_URL%/}/system_stats"
if ! CSTATS="$(curl -fsS --max-time 8 "${COMFYUI_URL%/}/system_stats" 2>/dev/null)"; then
  CSTATS="{}"
  warn "ComfyUI API is unavailable; stable-diffusion.cpp may still satisfy production readiness"
fi

python3 - "$ZHEALTH" "$CSTATS" <<'PY'
import json
import sys

health = json.loads(sys.argv[1])
try:
    stats = json.loads(sys.argv[2])
except json.JSONDecodeError:
    stats = {}
comfy = health.get("comfyui", {}) or {}
sdcpp = health.get("sdcpp", {}) or {}
system = stats.get("system", {}) if isinstance(stats, dict) else {}
devices = stats.get("devices", []) if isinstance(stats, dict) else []
devices = devices or []


def yes(value):
    return "YES" if bool(value) else "NO"


print("\n=== zMovie Production Doctor ===")
print(f"service_status         : {health.get('status', 'unknown')}")
print(f"ffmpeg                : {yes(health.get('ffmpeg'))}")
print(f"ffprobe               : {yes(health.get('ffprobe'))}")
print(f"render_ready           : {yes(health.get('render_ready'))}")
print(f"production_video_ready : {yes(health.get('production_video_ready'))}")
print(f"production_backends    : {', '.join(health.get('production_backends') or []) or 'none'}")

print("\n--- ComfyUI ---")
print(f"reachable              : {yes(comfy.get('reachable'))}")
print(f"workflow_configured    : {yes(comfy.get('configured'))}")
print(f"workflow_role          : {comfy.get('workflow_role', 'generic')}")
print(f"workflow_valid         : {yes(comfy.get('workflow_valid'))}")
print(f"nodes_available        : {yes(comfy.get('nodes_available'))}")
print(f"accelerated            : {yes(comfy.get('accelerated'))}")
print(f"comfyui_version        : {system.get('comfyui_version', 'unknown')}")
print("devices:")
for device in devices:
    if isinstance(device, dict):
        print(f"  - {device.get('name', 'unknown')} ({device.get('type', 'unknown')})")

print("\n--- stable-diffusion.cpp ---")
print(f"cli_available           : {yes(sdcpp.get('cli_available'))}")
print(f"video_enabled           : {yes(sdcpp.get('video_enabled'))}")
print(f"model_configured        : {yes(sdcpp.get('model_configured'))}")
print(f"model_files_valid       : {yes(sdcpp.get('model_files_valid'))}")
print(f"backend                 : {sdcpp.get('backend', 'auto')}")
print(f"vulkan_available        : {yes(sdcpp.get('vulkan_available'))}")
print(f"cpu_available           : {yes(sdcpp.get('cpu_available'))}")
print(f"production_ready        : {yes(sdcpp.get('production_ready'))}")
reasons = sdcpp.get("reasons") or []
if reasons:
    print("sdcpp blockers:")
    for reason in reasons:
        print(f"  - {reason}")

if health.get("production_video_ready"):
    print("\nPROFILE: PRODUCTION_VIDEO_RENDER_HOST")
    print("At least one real video provider passed its provider-specific readiness gate.")
    print("Next: run a short production render; the resulting file must still pass ffprobe media validation.")
elif sdcpp.get("cli_available"):
    print("\nPROFILE: LOCAL_SDCPP_ENGINE")
    print("stable-diffusion.cpp is installed, but its video model/runtime configuration is not production-ready yet.")
    print("Configure an explicit video model bundle; CPU is allowed and Vulkan is preferred when available.")
elif comfy.get("accelerated"):
    print("\nPROFILE: ACCELERATED_RENDER_HOST")
    print("ComfyUI acceleration is available, but a workflow explicitly classified as role=video is still required.")
else:
    print("\nPROFILE: CPU_ONLY_RENDER_HOST")
    print("No production-ready video provider is configured yet.")
    print("Options: install stable-diffusion.cpp for CPU/Vulkan, or configure a private accelerated ComfyUI/video gateway.")

missing = comfy.get("missing_node_types") or []
if missing:
    print("\nMISSING COMFYUI NODE TYPES:")
    for node in missing:
        print(f"  - {node}")

if not health.get("render_ready"):
    sys.exit(3)
PY

log "doctor completed"
