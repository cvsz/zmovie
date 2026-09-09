#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
LOCK_DIR="${ZMOVIE_PRODUCTION_RELEASE_LOCK:-/var/lib/zmovie/.production-release.lock}"

TITLE="ZeaZDev × Bilibili | Full Ads Production — zMovie"
DESCRIPTION="ZeaZDev × Bilibili creator publishing campaign featuring zMovie — a self-hosted production platform covering concept development, storyboarding, rendering, QC, FFmpeg assembly, controlled approval, and creator-platform publishing. This campaign creative was produced by ZeaZDev and is prepared for publishing through Bilibili Creator Center. ‘ZeaZDev × Bilibili’ is campaign creative wording and does not imply an official partnership, sponsorship, or endorsement by Bilibili."
TAGS="zMovie,ZeaZDev,Creator Tools,Video Production,Bilibili"

log(){ printf '[zMovie production-release] %s\n' "$*"; }
fail(){ printf '[zMovie production-release] ERROR: %s\n' "$*" >&2; exit 1; }
quote(){ printf '%q' "$1"; }

[[ ${EUID} -eq 0 ]] || fail "run as root, for example: sudo bash $0"
[[ -d "$INSTALL_DIR" ]] || fail "install directory not found: $INSTALL_DIR"
[[ -f "$ENV_FILE" ]] || fail "environment file not found: $ENV_FILE"
[[ -x "$INSTALL_DIR/.venv/bin/python" ]] || fail "Python runtime not found: $INSTALL_DIR/.venv/bin/python"
[[ -x "$INSTALL_DIR/scripts/production-gen.sh" || -f "$INSTALL_DIR/scripts/production-gen.sh" ]] || fail "production-gen.sh not installed; upgrade zMovie first"
[[ -f "$INSTALL_DIR/scripts/verify-bilibili-session.sh" ]] || fail "Bilibili session verifier not installed"
id "$SERVICE_USER" >/dev/null 2>&1 || fail "service user not found: $SERVICE_USER"
command -v ffprobe >/dev/null 2>&1 || fail "ffprobe not found"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum not found"
command -v python3 >/dev/null 2>&1 || fail "python3 not found"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  fail "another production release appears to be running: $LOCK_DIR"
fi
GEN_FILE="$(mktemp)"
PREPARE_FILE="$(mktemp)"
PROBE_FILE="$(mktemp)"
cleanup(){
  rm -f "$GEN_FILE" "$PREPARE_FILE" "$PROBE_FILE"
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

log "step 1/5: generating a fresh exact 30-second production candidate"
bash "$INSTALL_DIR/scripts/production-gen.sh" | tee "$GEN_FILE"

PROJECT_ID="$(sed -n 's/^project_id=//p' "$GEN_FILE" | tail -n1)"
FINAL_PATH="$(sed -n 's/^final_path=//p' "$GEN_FILE" | tail -n1)"
[[ "$PROJECT_ID" =~ ^prj_[A-Za-z0-9]+$ ]] || fail "could not resolve a safe production project_id"
[[ -f "$FINAL_PATH" ]] || fail "generated final asset not found: $FINAL_PATH"

log "step 2/5: verifying scoped live Bilibili Creator Center session"
bash "$INSTALL_DIR/scripts/verify-bilibili-session.sh"

log "step 3/5: preparing exact Bilibili package without approval or upload"
PREPARE_CMD="cd $(quote "$INSTALL_DIR"); set -a; source $(quote "$ENV_FILE"); set +a; export ZMOVIE_BILIBILI_AUTO_PUBLISH=false; exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened prepare --project $(quote "$PROJECT_ID") --title $(quote "$TITLE") --description $(quote "$DESCRIPTION") --tags $(quote "$TAGS")"
runuser -u "$SERVICE_USER" -- bash -lc "$PREPARE_CMD" >"$PREPARE_FILE"
cat "$PREPARE_FILE"

readarray -t PACKAGE_FIELDS < <(python3 - "$PREPARE_FILE" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
job_id = str(data.get("id") or "")
status = str(data.get("status") or "")
video = str(data.get("video_path") or "")
cover = str(data.get("cover_path") or "")
if not job_id.startswith("pub_"):
    raise SystemExit("prepared package returned an invalid publish job id")
if status != "prepared":
    raise SystemExit(f"package must stop at prepared status, got {status!r}")
if not video or not cover:
    raise SystemExit("prepared package is missing video or cover path")
print(job_id)
print(status)
print(video)
print(cover)
PY
)

JOB_ID="${PACKAGE_FIELDS[0]:-}"
PACKAGE_STATUS="${PACKAGE_FIELDS[1]:-}"
PACKAGE_VIDEO="${PACKAGE_FIELDS[2]:-}"
COVER_PATH="${PACKAGE_FIELDS[3]:-}"
[[ "$JOB_ID" =~ ^pub_[A-Za-z0-9]+$ ]] || fail "invalid prepared publish job id: $JOB_ID"
[[ "$PACKAGE_STATUS" == "prepared" ]] || fail "unexpected package status: $PACKAGE_STATUS"
[[ -f "$PACKAGE_VIDEO" ]] || fail "prepared video not found: $PACKAGE_VIDEO"
[[ -f "$COVER_PATH" ]] || fail "prepared cover not found: $COVER_PATH"
[[ "$(readlink -f "$PACKAGE_VIDEO")" == "$(readlink -f "$FINAL_PATH")" ]] || fail "prepared package does not reference the newly generated final.mp4"

log "step 4/5: running local media/package QC"
ffprobe -v error \
  -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels:format=duration,size \
  -of json \
  "$PACKAGE_VIDEO" >"$PROBE_FILE"

python3 - "$PROBE_FILE" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
streams = list(data.get("streams") or [])
video = next((x for x in streams if x.get("codec_type") == "video"), {})
audio = next((x for x in streams if x.get("codec_type") == "audio"), {})
fmt = data.get("format") or {}
duration = float(fmt.get("duration") or 0)
errors = []
if abs(duration - 30.0) > 0.15:
    errors.append(f"duration={duration:.3f}s")
if video.get("codec_name") != "h264":
    errors.append(f"video_codec={video.get('codec_name')!r}")
if int(video.get("width") or 0) != 1280 or int(video.get("height") or 0) != 720:
    errors.append(f"resolution={video.get('width')}x{video.get('height')}")
if audio.get("codec_name") != "aac":
    errors.append(f"audio_codec={audio.get('codec_name')!r}")
if int(audio.get("sample_rate") or 0) != 48000:
    errors.append(f"sample_rate={audio.get('sample_rate')!r}")
if int(audio.get("channels") or 0) != 2:
    errors.append(f"channels={audio.get('channels')!r}")
if errors:
    raise SystemExit("production media QC failed: " + ", ".join(errors))
print(f"media_qc=PASS duration={duration:.3f}s video=h264 1280x720 audio=aac/48000Hz/stereo")
PY

COVER_PROBE="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$COVER_PATH")"
[[ "$COVER_PROBE" == "1280x720" ]] || fail "cover must be 1280x720, got ${COVER_PROBE:-unknown}"

VIDEO_SHA256="$(sha256sum "$PACKAGE_VIDEO" | awk '{print $1}')"
COVER_SHA256="$(sha256sum "$COVER_PATH" | awk '{print $1}')"
MANIFEST_PATH="$(dirname "$COVER_PATH")/publication.json"
MANIFEST_SHA256=""
if [[ -f "$MANIFEST_PATH" ]]; then
  MANIFEST_SHA256="$(sha256sum "$MANIFEST_PATH" | awk '{print $1}')"
fi

log "step 5/5: release package prepared; stopping at the human approval gate"
printf '%s\n' \
  "project_id=$PROJECT_ID" \
  "publish_job_id=$JOB_ID" \
  "status=prepared" \
  "final_path=$PACKAGE_VIDEO" \
  "cover_path=$COVER_PATH" \
  "video_sha256=$VIDEO_SHA256" \
  "cover_sha256=$COVER_SHA256" \
  "manifest_path=$MANIFEST_PATH" \
  "manifest_sha256=${MANIFEST_SHA256:-not_available}" \
  "studio=https://zmovie.zeaz.dev/studio" \
  "approval=NOT PERFORMED" \
  "upload=NOT PERFORMED" \
  "publication=NOT PERFORMED"

log "STOP: listen to the exact 30-second asset and review title/description/cover before approval"
log "after explicit approval, run: sudo -u $SERVICE_USER bash -lc 'cd $INSTALL_DIR; set -a; source $ENV_FILE; set +a; .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened approve --job $JOB_ID'"
log "then run fail-closed preflight: sudo bash $INSTALL_DIR/scripts/preflight-bilibili-publish.sh $JOB_ID"
