#!/usr/bin/env bash
set -Eeuo pipefail

ZMOVIE_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ZMOVIE_ENV="${ZMOVIE_ENV_FILE:-/etc/zmovie/zmovie.env}"
ZMOVIE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
PROJECT_ID="${1:-}"

log(){ printf '[zMovie Bilibili package smoke] %s\n' "$*"; }
fail(){ printf '[zMovie Bilibili package smoke] ERROR: %s\n' "$*" >&2; exit 1; }

[[ "$EUID" -eq 0 ]] || fail "run with sudo"
[[ -x "${ZMOVIE_DIR}/.venv/bin/python" ]] || fail "zMovie venv not found at ${ZMOVIE_DIR}/.venv"
[[ -f "$ZMOVIE_ENV" ]] || fail "zMovie env file not found: $ZMOVIE_ENV"
command -v ffprobe >/dev/null 2>&1 || fail "ffprobe is required"

log "preparing publication package without browser login or publication"
runuser -u "$ZMOVIE_USER" -- bash -c "set -a; source '$ZMOVIE_ENV'; set +a; cd '$ZMOVIE_DIR'; exec .venv/bin/python - '$PROJECT_ID'" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from zmovie_platform.publishers.bilibili import PUBLISH_ROOT, prepare_bilibili_publish
from zmovie_platform.storage import connect

project_id = sys.argv[1].strip()
if not project_id:
    with connect() as conn:
        row = conn.execute(
            "SELECT project_id FROM assets WHERE kind='final' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
    if row is None:
        raise SystemExit("no final project asset found; run smoke-project-assembly.sh first or pass PROJECT_ID")
    project_id = str(row[0])

job = prepare_bilibili_publish(project_id)
if job.get("status") != "prepared":
    raise SystemExit("publication job was not left in prepared state: " + json.dumps(job, ensure_ascii=False))

video = Path(str(job.get("video_path", "")))
cover = Path(str(job.get("cover_path", "")))
manifest = PUBLISH_ROOT / project_id / str(job["id"]) / "publication.json"
for label, path in (("video", video), ("cover", cover), ("manifest", manifest)):
    if not path.is_file():
        raise SystemExit(f"{label} file missing: {path}")

probe = subprocess.run(
    [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height", "-of", "json", str(cover),
    ],
    check=True,
    capture_output=True,
    text=True,
)
cover_info = json.loads(probe.stdout)
streams = cover_info.get("streams") or []
if not streams:
    raise SystemExit("generated cover has no video/image stream")
stream = streams[0]
if int(stream.get("width", 0)) != 1280 or int(stream.get("height", 0)) != 720:
    raise SystemExit(f"generated cover is not 1280x720: {stream}")

if len(str(job.get("title", ""))) > 100:
    raise SystemExit("title exceeds Bilibili limit")
if len(str(job.get("description", ""))) > 2000:
    raise SystemExit("description exceeds Bilibili limit")
if len(job.get("tags") or []) > 10:
    raise SystemExit("tag count exceeds Bilibili limit")

print(json.dumps(job, ensure_ascii=False, indent=2))
print(f"PROJECT_ID={project_id}")
print(f"PUB_JOB_ID={job['id']}")
print(f"VIDEO={video}")
print(f"COVER={cover}")
print(f"MANIFEST={manifest}")
PY

log "PASS: final movie -> cover -> metadata -> publication manifest -> prepared publish job"
log "No Google/Bilibili login was used and nothing was uploaded or published."
