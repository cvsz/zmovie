#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"

log(){ printf '[zMovie Bilibili candidates] %s\n' "$*"; }
fail(){ printf '[zMovie Bilibili candidates] ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || fail "run as root, for example: sudo bash $0"
[[ -f "$ENV_FILE" ]] || fail "zMovie environment not found: $ENV_FILE"
[[ -x "$INSTALL_DIR/.venv/bin/python" ]] || fail "zMovie Python not found: $INSTALL_DIR/.venv/bin/python"
id "$SERVICE_USER" >/dev/null 2>&1 || fail "service user not found: $SERVICE_USER"

log "listing projects with managed final video assets; no publication state is changed"

# Keep the Python program outside the quoted bash -c payload. The previous
# implementation embedded a heredoc inside a double-quoted shell string,
# allowing shell quote processing to corrupt Python f-strings before execution.
runuser -u "$SERVICE_USER" -- \
  env ZMOVIE_CANDIDATE_INSTALL_DIR="$INSTALL_DIR" ZMOVIE_CANDIDATE_ENV_FILE="$ENV_FILE" \
  bash -c '
    set -Eeuo pipefail
    cd "$ZMOVIE_CANDIDATE_INSTALL_DIR"
    set -a
    # shellcheck disable=SC1090
    source "$ZMOVIE_CANDIDATE_ENV_FILE"
    set +a
    exec .venv/bin/python -
  ' <<'PY'
import json
import shutil
import subprocess
from pathlib import Path

from zmovie_platform.repository import get_project, list_assets, list_projects

markers = ("smoke", "mock", "test", "dry run", "dry-run", "example", "demo")
rows = []
ffprobe = shutil.which("ffprobe")

for item in list_projects(limit=500):
    project_id = str(item["id"])
    project = get_project(project_id)
    if project is None:
        continue

    finals = list_assets(project_id, "final")
    for asset in finals:
        path = Path(str(asset.get("path") or "")).expanduser()
        if not path.is_file():
            continue

        text = f"{project.name} {project.concept}".lower()
        marker_hits = sorted({marker for marker in markers if marker in text})
        media = {
            "codec": "",
            "width": 0,
            "height": 0,
            "duration_seconds": 0.0,
        }

        if not ffprobe:
            media["ffprobe_error"] = "ffprobe is not installed"
        else:
            try:
                proc = subprocess.run(
                    [
                        ffprobe,
                        "-v",
                        "error",
                        "-select_streams",
                        "v:0",
                        "-show_entries",
                        "stream=codec_name,width,height:format=duration",
                        "-of",
                        "json",
                        str(path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=True,
                )
                data = json.loads(proc.stdout or "{}")
                streams = list(data.get("streams") or [])
                stream = streams[0] if streams else {}
                fmt = dict(data.get("format") or {})
                media = {
                    "codec": str(stream.get("codec_name") or ""),
                    "width": int(stream.get("width") or 0),
                    "height": int(stream.get("height") or 0),
                    "duration_seconds": round(float(fmt.get("duration") or 0.0), 3),
                }
            except Exception as exc:
                media["ffprobe_error"] = str(exc)[:200]

        rows.append(
            {
                "project_id": project_id,
                "name": project.name,
                "final_asset_id": asset.get("id"),
                "final_path": str(path.resolve()),
                "candidate": (
                    not marker_hits
                    and media.get("width", 0) > 0
                    and media.get("height", 0) > 0
                    and media.get("duration_seconds", 0) > 0
                ),
                "blocked_markers": marker_hits,
                "media": media,
            }
        )

rows.sort(key=lambda row: (not row["candidate"], row["name"].casefold(), row["project_id"]))
print(json.dumps({"count": len(rows), "items": rows}, ensure_ascii=False, indent=2))
PY
