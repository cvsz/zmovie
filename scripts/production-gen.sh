#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
LOCK_DIR="${ZMOVIE_PRODUCTION_GEN_LOCK:-/var/lib/zmovie/.production-gen.lock}"
BACKUP_DIR="${ZMOVIE_PRODUCTION_GEN_BACKUP_DIR:-/var/backups/zmovie}"

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

DB_PATH="$(sed -n 's/^ZMOVIE_DB_PATH=//p' "$ENV_FILE" | tail -n1)"
DB_PATH="${DB_PATH:-/var/lib/zmovie/zmovie.db}"
install -d -o root -g "$SERVICE_USER" -m 0750 "$BACKUP_DIR"
if [[ -f "$DB_PATH" ]]; then
  STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
  BACKUP_FILE="$BACKUP_DIR/zmovie-production-gen-${STAMP}-$$.db"
  python3 - "$DB_PATH" "$BACKUP_FILE" <<'PY'
import sqlite3
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
temp = target.with_suffix(target.suffix + ".tmp")
temp.unlink(missing_ok=True)
try:
    with sqlite3.connect(source) as src, sqlite3.connect(temp) as dst:
        src.backup(dst)
    with sqlite3.connect(temp) as check:
        result = check.execute("PRAGMA quick_check").fetchone()
        if result is None or str(result[0]).lower() != "ok":
            raise SystemExit(f"SQLite integrity check failed: {result}")
        violations = check.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise SystemExit(f"SQLite foreign-key check failed: {violations[:10]}")
    temp.replace(target)
finally:
    temp.unlink(missing_ok=True)
PY
  chmod 0640 "$BACKUP_FILE"
  chown root:"$SERVICE_USER" "$BACKUP_FILE"
  log "database backup: $BACKUP_FILE"
else
  log "database does not exist yet; pre-generation backup skipped"
fi

log "profile: Thai neural voice + soft background music, exact 30-second output"
log "timeline: 1.2s music intro, narration with ducked music, at least 1.5s music outro"
log "voice: th-TH-PremwadeeNeural at -19%; local robotic fallback disabled"
log "music: soft background gain 0.04 with sidechain ducking under narration"
log "idempotency: stale exact-match unapproved candidates are superseded only after a new candidate passes QC"
log "protected publish states are preserved; no Bilibili upload, approval, or publication will be performed"

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
cleanup = profile.get("supersede_cleanup") or {}
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
print(f"voice_start_seconds={profile.get('voice_start_seconds')}")
print(f"tts_voice={profile.get('tts_voice')} rate={profile.get('tts_rate')}")
print(f"music_gain={profile.get('music_gain')}")
print(f"profile={profile.get('profile')}")
print(f"superseded_projects={len(cleanup.get('deleted') or [])}")
print(f"preserved_protected_projects={len(cleanup.get('preserved') or [])}")
print(f"cleanup_complete={bool(cleanup.get('cleanup_complete'))}")
for item in cleanup.get("preserved") or []:
    print(
        "preserved_project="
        f"{item.get('project_id')} statuses={','.join(item.get('statuses') or [])}"
    )
for error in cleanup.get("errors") or []:
    print(f"cleanup_warning={error}")
print("publication=NOT PERFORMED")
PY
then
  cat "$RESULT_FILE" >&2
  fail "production result validation failed"
fi

log "candidate is ready for manual Studio listening/review"
log "Studio: https://zmovie.zeaz.dev/studio"
log "next gate: review the exact asset before creating or approving any Bilibili publish job"
