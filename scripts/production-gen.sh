#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
LOCK_DIR="${ZMOVIE_PRODUCTION_GEN_LOCK:-/var/lib/zmovie/.production-gen.lock}"

log(){ printf '[zMovie production-gen] %s\n' "$*"; }
fail(){ printf '[zMovie production-gen] ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || fail "run as root, for example: sudo bash $0"
[[ -d "$INSTALL_DIR" ]] || fail "install directory not found: $INSTALL_DIR"
[[ -f "$ENV_FILE" ]] || fail "environment file not found: $ENV_FILE"
[[ -x "$INSTALL_DIR/.venv/bin/python" ]] || fail "Python runtime not found: $INSTALL_DIR/.venv/bin/python"
[[ -f "$INSTALL_DIR/zmovie_platform/publishers/production_gen.py" ]] || fail "production generator module not installed; upgrade zMovie first"
id "$SERVICE_USER" >/dev/null 2>&1 || fail "service user not found: $SERVICE_USER"
command -v ffmpeg >/dev/null 2>&1 || fail "ffmpeg not found"
command -v ffprobe >/dev/null 2>&1 || fail "ffprobe not found"
command -v python3 >/dev/null 2>&1 || fail "python3 not found"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  fail "another production generation appears to be running: $LOCK_DIR"
fi
RESULT_FILE="$(mktemp)"
cleanup(){
  rm -f "$RESULT_FILE"
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

log "profile: Thai neural voice + music, exact 30-second output"
log "voice: th-TH-PremwadeeNeural at -15%; local robotic fallback disabled"
log "no Bilibili upload, approval, or publication will be performed"

runuser -u "$SERVICE_USER" -- bash -lc "
  cd '$INSTALL_DIR'
  set -a
  source '$ENV_FILE'
  set +a
  export ZMOVIE_TTS_PROVIDER=edge
  export ZMOVIE_TTS_VOICE=th-TH-PremwadeeNeural
  export ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK=false
  exec .venv/bin/python -m zmovie_platform.publishers.production_gen
" >"$RESULT_FILE"

if ! python3 - "$RESULT_FILE" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
raw = path.read_text(encoding="utf-8")
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    print(raw, file=sys.stderr)
    raise SystemExit("production generator did not return valid JSON")

media = data.get("media") or {}
profile = data.get("production_gen") or {}
asset = data.get("final_asset") or {}
final_path = Path(str(asset.get("path") or ""))
if not final_path.is_file():
    raise SystemExit(f"final asset missing: {final_path}")

print("[zMovie production-gen] SUCCESS")
print(f"project_id={data.get('project_id')}")
print(f"final_path={final_path}")
print(f"duration_seconds={float(media.get('duration_seconds') or 0):.3f}")
print(f"video={media.get('codec')} {media.get('width')}x{media.get('height')} {media.get('frame_rate')}")
print(f"audio={media.get('audio_codec')} {media.get('audio_sample_rate')}Hz channels={media.get('audio_channels')}")
print(f"voice_preflight_seconds={profile.get('voice_preflight_seconds')}")
print(f"tts_voice={profile.get('tts_voice')} rate={profile.get('tts_rate')}")
print(f"profile={profile.get('profile')}")
print("publication=NOT PERFORMED")
PY
then
  cat "$RESULT_FILE" >&2
  fail "production result validation failed"
fi

log "candidate is ready for manual Studio listening/review"
log "Studio: https://zmovie.zeaz.dev/studio"
log "next gate: review the exact asset before creating or approving any Bilibili publish job"
