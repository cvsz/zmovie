#!/usr/bin/env bash
set -Eeuo pipefail

ZMOVIE_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ZMOVIE_ENV="${ZMOVIE_ENV_FILE:-/etc/zmovie/zmovie.env}"
ZMOVIE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
COMFYUI_DIR="${COMFYUI_INSTALL_DIR:-/opt/comfyui}"
COMFYUI_DATA="${COMFYUI_DATA_DIR:-/var/lib/comfyui}"
COMFYUI_USER="${COMFYUI_SERVICE_USER:-comfyui}"
COMFYUI_URL="${ZMOVIE_COMFYUI_URL:-http://127.0.0.1:8188}"
SMOKE_WORKFLOW="${ZMOVIE_DIR}/workflows/comfyui/smoke_api.json"
SMOKE_IMAGE="${COMFYUI_DATA}/input/zmovie-smoke.png"

log(){ printf '[zMovie/ComfyUI smoke] %s\n' "$*"; }
fail(){ printf '[zMovie/ComfyUI smoke] ERROR: %s\n' "$*" >&2; exit 1; }

[[ "$EUID" -eq 0 ]] || fail "run with sudo"
[[ -x "${COMFYUI_DIR}/.venv/bin/python" ]] || fail "ComfyUI venv not found at ${COMFYUI_DIR}/.venv"
[[ -x "${ZMOVIE_DIR}/.venv/bin/python" ]] || fail "zMovie venv not found at ${ZMOVIE_DIR}/.venv"
[[ -f "$ZMOVIE_ENV" ]] || fail "zMovie env file not found: $ZMOVIE_ENV"
[[ -f "$SMOKE_WORKFLOW" ]] || fail "smoke workflow not found: $SMOKE_WORKFLOW (upgrade zMovie first)"

log "checking ComfyUI API"
curl -fsS --max-time 5 "${COMFYUI_URL%/}/system_stats" >/dev/null || fail "ComfyUI is not reachable at $COMFYUI_URL"

log "creating model-free smoke input image"
install -d -o "$COMFYUI_USER" -g "$COMFYUI_USER" -m 0750 "${COMFYUI_DATA}/input"
"${COMFYUI_DIR}/.venv/bin/python" - "$SMOKE_IMAGE" <<'PY'
import sys
from pathlib import Path
from PIL import Image, ImageDraw

path = Path(sys.argv[1])
image = Image.new("RGB", (640, 360), (18, 24, 38))
draw = ImageDraw.Draw(image)
draw.rectangle((24, 24, 616, 336), outline=(130, 160, 255), width=4)
draw.text((48, 150), "zMovie -> ComfyUI smoke test", fill=(238, 243, 255))
image.save(path, "PNG")
PY
chown "$COMFYUI_USER:$COMFYUI_USER" "$SMOKE_IMAGE"
chmod 0640 "$SMOKE_IMAGE"

log "configuring zMovie with the smoke API workflow"
bash "${ZMOVIE_DIR}/scripts/configure-comfyui.sh" "$SMOKE_WORKFLOW" "$COMFYUI_URL"

log "submitting through the zMovie ComfyUI provider and downloading the output"
runuser -u "$ZMOVIE_USER" -- bash -c "set -a; source '$ZMOVIE_ENV'; set +a; cd '$ZMOVIE_DIR'; exec .venv/bin/python -" <<'PY'
from __future__ import annotations

import json
import uuid
from pathlib import Path

from zmovie_platform.providers import COMFYUI

job_id = "smoke-" + uuid.uuid4().hex[:12]
output_dir = Path("/var/lib/zmovie/media/comfyui-smoke")
result = COMFYUI.submit(
    prompt="zMovie ComfyUI model-free smoke test",
    negative_prompt="",
    output_dir=output_dir,
    metadata={
        "job_id": job_id,
        "project_id": "smoke",
        "shot_id": "smoke",
        "duration_seconds": 1,
        "aspect_ratio": "16:9",
    },
)
path = Path(str(result.get("output_path", "")))
if result.get("status") != "completed" or not path.is_file():
    raise SystemExit("smoke provider did not produce a downloaded output: " + json.dumps(result, ensure_ascii=False))
print(json.dumps(result, ensure_ascii=False, indent=2))
print(f"SMOKE_OUTPUT={path}")
PY

log "PASS: zMovie queued ComfyUI, observed history, and downloaded a generated output."
log "This workflow is only a connectivity smoke test; replace it with your production video workflow next."
