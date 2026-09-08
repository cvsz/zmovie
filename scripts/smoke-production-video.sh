#!/usr/bin/env bash
set -Eeuo pipefail

ZMOVIE_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ZMOVIE_ENV="${ZMOVIE_ENV_FILE:-/etc/zmovie/zmovie.env}"
ZMOVIE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
ZMOVIE_URL="${ZMOVIE_URL:-http://127.0.0.1:8080}"
PROMPT="${1:-A cinematic five-second establishing shot of a futuristic city at sunrise, stable camera motion, realistic lighting, coherent geometry.}"

log(){ printf '[zMovie production-video smoke] %s\n' "$*"; }
fail(){ printf '[zMovie production-video smoke] ERROR: %s\n' "$*" >&2; exit 1; }

[[ "$EUID" -eq 0 ]] || fail "run with sudo"
[[ -x "${ZMOVIE_DIR}/.venv/bin/python" ]] || fail "zMovie venv not found"
[[ -f "$ZMOVIE_ENV" ]] || fail "zMovie env file not found"
command -v curl >/dev/null 2>&1 || fail "curl is required"
command -v ffprobe >/dev/null 2>&1 || fail "ffprobe is required"

log "checking production video readiness"
HEALTH="$(curl -fsS --max-time 8 "${ZMOVIE_URL%/}/api/v2/health")" || fail "zMovie health endpoint unavailable"
printf '%s\n' "$HEALTH" | python3 -m json.tool
READY="$(printf '%s' "$HEALTH" | python3 -c 'import json,sys; print(str(bool(json.load(sys.stdin).get("production_video_ready"))).lower())')"
[[ "$READY" == "true" ]] || fail "production_video_ready=false; configure an accelerated ComfyUI host with a role=video workflow first"

log "submitting a real short-shot render through the zMovie ComfyUI provider"
RESULT="$(runuser -u "$ZMOVIE_USER" -- bash -c "set -a; source '$ZMOVIE_ENV'; set +a; cd '$ZMOVIE_DIR'; exec .venv/bin/python - '$PROMPT'" <<'PY'
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

from zmovie_platform.providers import COMFYUI

prompt = sys.argv[1]
job_id = "production-smoke-" + uuid.uuid4().hex[:12]
output_dir = Path("/var/lib/zmovie/media/comfyui-production-smoke")
result = COMFYUI.submit(
    prompt=prompt,
    negative_prompt="identity drift, geometry errors, flicker, duplicated objects, text artifacts, low quality",
    output_dir=output_dir,
    metadata={
        "job_id": job_id,
        "project_id": "production-smoke",
        "shot_id": "production-smoke",
        "duration_seconds": 5,
        "aspect_ratio": "16:9",
    },
)
path = Path(str(result.get("output_path", "")))
if result.get("status") != "completed":
    raise SystemExit("render did not complete: " + json.dumps(result, ensure_ascii=False))
if result.get("kind") != "video":
    raise SystemExit("production workflow did not return a video: " + json.dumps(result, ensure_ascii=False))
if not path.is_file() or path.stat().st_size <= 0:
    raise SystemExit(f"video output missing or empty: {path}")
print(json.dumps({"result": result, "output_path": str(path)}, ensure_ascii=False))
PY
)" || fail "zMovie production render failed"

OUTPUT_PATH="$(printf '%s' "$RESULT" | python3 -c 'import json,sys; print(json.load(sys.stdin)["output_path"])')"
[[ -f "$OUTPUT_PATH" ]] || fail "render output not found: $OUTPUT_PATH"

log "validating video stream with ffprobe"
PROBE="$(ffprobe -v error -show_streams -show_format -of json "$OUTPUT_PATH")" || fail "ffprobe failed"
printf '%s\n' "$PROBE" | python3 -m json.tool
python3 - "$PROBE" <<'PY'
import json
import sys
payload = json.loads(sys.argv[1])
streams = payload.get("streams") or []
video = [s for s in streams if s.get("codec_type") == "video"]
if not video:
    raise SystemExit("no video stream found")
duration = payload.get("format", {}).get("duration")
try:
    duration_value = float(duration)
except (TypeError, ValueError):
    duration_value = 0.0
if duration_value <= 0:
    raise SystemExit("video duration is not positive")
print(f"validated video codec={video[0].get('codec_name','unknown')} duration={duration_value:.3f}s")
PY

log "PASS: real accelerated ComfyUI video rendered through zMovie and passed ffprobe validation"
printf 'PRODUCTION_VIDEO_OUTPUT=%s\n' "$OUTPUT_PATH"
