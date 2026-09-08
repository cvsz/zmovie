#!/usr/bin/env bash
set -Eeuo pipefail

ZMOVIE_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ZMOVIE_ENV="${ZMOVIE_ENV_FILE:-/etc/zmovie/zmovie.env}"
ZMOVIE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"

log(){ printf '[zMovie project smoke] %s\n' "$*"; }
fail(){ printf '[zMovie project smoke] ERROR: %s\n' "$*" >&2; exit 1; }

[[ "$EUID" -eq 0 ]] || fail "run with sudo"
[[ -x "${ZMOVIE_DIR}/.venv/bin/python" ]] || fail "zMovie venv not found"
[[ -f "$ZMOVIE_ENV" ]] || fail "zMovie env file not found"
command -v ffprobe >/dev/null 2>&1 || fail "ffprobe is required"

log "running storyboard -> QC -> mock render -> FFmpeg assembly"
RESULT="$(runuser -u "$ZMOVIE_USER" -- bash -c "set -a; source '$ZMOVIE_ENV'; set +a; cd '$ZMOVIE_DIR'; exec .venv/bin/python -" <<'PY'
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from zmovie_platform.pipeline import run_end_to_end

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
result = run_end_to_end(
    name=f"Production pipeline smoke {stamp}",
    concept="A short cinematic continuity test: a courier crosses a neon-lit rooftop, pauses at the edge, then watches sunrise over the city.",
    genre="cinematic action",
    visual_style="photorealistic premium cinematic realism",
    aspect_ratio="16:9",
    target_duration_seconds=10,
    provider="mock",
    owner="production-smoke",
)
assembly = result.get("assembly") or {}
path = Path(str(assembly.get("output_path", "")))
if not result.get("qc", {}).get("passed"):
    raise SystemExit("QC failed: " + json.dumps(result.get("qc"), ensure_ascii=False))
if result.get("render", {}).get("status") != "completed":
    raise SystemExit("mock render failed: " + json.dumps(result.get("render"), ensure_ascii=False))
if not path.is_file() or path.stat().st_size <= 0:
    raise SystemExit("assembly output missing: " + json.dumps(assembly, ensure_ascii=False))
print(json.dumps({
    "project_id": result["project"]["id"],
    "qc_score": result["qc"].get("score"),
    "render_status": result["render"].get("status"),
    "assembly": assembly,
    "output_path": str(path),
}, ensure_ascii=False))
PY
)" || fail "project pipeline smoke failed"

OUTPUT_PATH="$(printf '%s' "$RESULT" | python3 -c 'import json,sys; print(json.load(sys.stdin)["output_path"])')"
PROJECT_ID="$(printf '%s' "$RESULT" | python3 -c 'import json,sys; print(json.load(sys.stdin)["project_id"])')"
log "validating assembled movie with ffprobe"
PROBE="$(ffprobe -v error -show_streams -show_format -of json "$OUTPUT_PATH")" || fail "ffprobe failed"
printf '%s\n' "$PROBE" | python3 -m json.tool
python3 - "$PROBE" <<'PY'
import json
import sys
payload = json.loads(sys.argv[1])
video = [stream for stream in payload.get("streams", []) if stream.get("codec_type") == "video"]
if not video:
    raise SystemExit("assembled output has no video stream")
try:
    duration = float(payload.get("format", {}).get("duration") or 0)
except (TypeError, ValueError):
    duration = 0
if duration <= 0:
    raise SystemExit("assembled output has invalid duration")
print(f"validated assembled video codec={video[0].get('codec_name','unknown')} duration={duration:.3f}s")
PY

log "PASS: project storyboard/QC/render/assembly pipeline produced a valid movie"
printf 'PROJECT_ID=%s\nFINAL_MOVIE=%s\n' "$PROJECT_ID" "$OUTPUT_PATH"
