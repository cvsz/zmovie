#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
BACKUP_DIR="${ZMOVIE_BACKUP_DIR:-/var/backups/zmovie}"
CONFIRM="${1:-}"

log(){ printf '[zMovie project reset] %s\n' "$*"; }
fail(){ printf '[zMovie project reset] ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || fail "run as root, for example: sudo bash $0 DELETE-ALL-PRJ"
[[ "$CONFIRM" == "DELETE-ALL-PRJ" ]] || fail "explicit confirmation required: DELETE-ALL-PRJ"
[[ -f "$ENV_FILE" ]] || fail "zMovie environment not found: $ENV_FILE"
[[ -x "$INSTALL_DIR/.venv/bin/python" ]] || fail "zMovie Python not found: $INSTALL_DIR/.venv/bin/python"
id "$SERVICE_USER" >/dev/null 2>&1 || fail "service user not found: $SERVICE_USER"
command -v ffprobe >/dev/null 2>&1 || fail "ffprobe not found"
command -v curl >/dev/null 2>&1 || fail "curl not found"

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

DB_PATH="${ZMOVIE_DB_PATH:?ZMOVIE_DB_PATH is required}"
MEDIA_ROOT="${ZMOVIE_MEDIA_ROOT:?ZMOVIE_MEDIA_ROOT is required}"
PUBLISH_ROOT="${ZMOVIE_PUBLISH_ROOT:?ZMOVIE_PUBLISH_ROOT is required}"
EXPORT_ROOT="${ZMOVIE_EXPORT_ROOT:?ZMOVIE_EXPORT_ROOT is required}"

mkdir -p "$BACKUP_DIR" "$MEDIA_ROOT" "$PUBLISH_ROOT" "$EXPORT_ROOT"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup="$BACKUP_DIR/zmovie-project-reset-$stamp.db"
quarantine="$(dirname "$DB_PATH")/.project-reset-$stamp"
mkdir -p "$quarantine/media" "$quarantine/publish" "$quarantine/exports"

service_was_active=0
if systemctl is-active --quiet zmovie; then
  service_was_active=1
  log "stopping zmovie for a consistent reset"
  systemctl stop zmovie
fi

committed=0
rollback(){
  rc=$?
  trap - EXIT
  if [[ "$committed" -eq 0 ]]; then
    log "reset did not commit; restoring previous database and project files"
    if [[ -f "$backup" ]]; then
      python3 - "$backup" "$DB_PATH" <<'PY'
import sqlite3, sys
from pathlib import Path
src = Path(sys.argv[1]); dst = Path(sys.argv[2])
with sqlite3.connect(src) as source, sqlite3.connect(dst) as destination:
    source.backup(destination)
PY
      chown "$SERVICE_USER:$SERVICE_USER" "$DB_PATH" || true
    fi
    for root_name in media publish exports; do
      qroot="$quarantine/$root_name"
      case "$root_name" in
        media) target_root="$MEDIA_ROOT" ;;
        publish) target_root="$PUBLISH_ROOT" ;;
        exports) target_root="$EXPORT_ROOT" ;;
      esac
      if [[ -d "$qroot" ]]; then
        find "$qroot" -mindepth 1 -maxdepth 1 -print0 | while IFS= read -r -d '' item; do
          mv -f -- "$item" "$target_root/" || true
        done
      fi
    done
  fi
  rm -rf -- "$quarantine" || true
  if [[ "$service_was_active" -eq 1 ]]; then
    systemctl start zmovie || true
  fi
  exit "$rc"
}
trap rollback EXIT

log "creating transactionally consistent SQLite backup: $backup"
python3 - "$DB_PATH" "$backup" <<'PY'
import sqlite3, sys
from pathlib import Path
source = Path(sys.argv[1]); target = Path(sys.argv[2])
target.unlink(missing_ok=True)
with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
    src.backup(dst)
with sqlite3.connect(target) as check:
    result = check.execute('PRAGMA quick_check').fetchone()
    if result is None or str(result[0]).lower() != 'ok':
        raise SystemExit(f'backup integrity check failed: {result}')
    violations = check.execute('PRAGMA foreign_key_check').fetchall()
    if violations:
        raise SystemExit(f'backup foreign-key check failed: {violations[:10]}')
PY
chmod 0640 "$backup"

log "listing project IDs selected by the exact prj_ guard"
mapfile -t project_ids < <(
  runuser -u "$SERVICE_USER" -- bash -lc "cd '$INSTALL_DIR'; set -a; source '$ENV_FILE'; set +a; exec .venv/bin/python -m zmovie_platform.project_reset list" \
    | python3 -c 'import json,sys; data=json.load(sys.stdin); [print(x) for x in data.get("project_ids", [])]'
)
printf '[zMovie project reset] database projects to remove: %s\n' "${#project_ids[@]}"
for project_id in "${project_ids[@]}"; do
  printf '  - %s\n' "$project_id"
done

move_if_exists(){
  local source="$1" destination="$2"
  [[ -e "$source" ]] || return 0
  mkdir -p "$destination"
  mv -- "$source" "$destination/"
}

quarantine_safe_project_entries(){
  local root="$1" destination="$2" allow_zip="${3:-false}"
  [[ -d "$root" ]] || return 0
  find "$root" -mindepth 1 -maxdepth 1 -print0 | while IFS= read -r -d '' item; do
    local name
    name="$(basename "$item")"
    if [[ "$name" =~ ^prj_[A-Za-z0-9]+$ ]]; then
      move_if_exists "$item" "$destination"
    elif [[ "$allow_zip" == "true" && "$name" =~ ^prj_[A-Za-z0-9]+\.zip$ ]]; then
      move_if_exists "$item" "$destination"
    fi
  done
}

log "quarantining DB-linked project files"
for project_id in "${project_ids[@]}"; do
  move_if_exists "$MEDIA_ROOT/$project_id" "$quarantine/media"
  move_if_exists "$PUBLISH_ROOT/$project_id" "$quarantine/publish"
  move_if_exists "$EXPORT_ROOT/$project_id" "$quarantine/exports"
  move_if_exists "$EXPORT_ROOT/$project_id.zip" "$quarantine/exports"
done

log "quarantining orphaned safe prj_* project files"
quarantine_safe_project_entries "$MEDIA_ROOT" "$quarantine/media"
quarantine_safe_project_entries "$PUBLISH_ROOT" "$quarantine/publish"
quarantine_safe_project_entries "$EXPORT_ROOT" "$quarantine/exports" true

log "deleting project rows with cascade semantics"
runuser -u "$SERVICE_USER" -- bash -lc "
  cd '$INSTALL_DIR'
  set -a
  source '$ENV_FILE'
  set +a
  exec .venv/bin/python -m zmovie_platform.project_reset delete --confirm DELETE-ALL-PRJ
"

log "creating one fresh production publication candidate"
runuser -u "$SERVICE_USER" -- bash -lc "
  cd '$INSTALL_DIR'
  set -a
  source '$ENV_FILE'
  set +a
  exec .venv/bin/python -m zmovie_platform.publishers.bilibili_launch_candidate
" | tee "$quarantine/new-project.json"

new_project_id="$(python3 - "$quarantine/new-project.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding='utf-8') as fh:
    print(json.load(fh)['project_id'])
PY
)"
[[ "$new_project_id" =~ ^prj_[A-Za-z0-9]+$ ]] || fail "new project id failed validation"
new_video="$MEDIA_ROOT/$new_project_id/final.mp4"
[[ -f "$new_video" ]] || fail "new production final.mp4 is missing: $new_video"

probe="$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height:format=duration -of json "$new_video")"
python3 - "$probe" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
stream = (data.get('streams') or [{}])[0]
duration = float((data.get('format') or {}).get('duration') or 0)
if not stream.get('codec_name') or int(stream.get('width') or 0) <= 0 or int(stream.get('height') or 0) <= 0 or duration <= 0:
    raise SystemExit('new production video failed ffprobe validation')
PY

count_json="$(runuser -u "$SERVICE_USER" -- bash -lc "cd '$INSTALL_DIR'; set -a; source '$ENV_FILE'; set +a; exec .venv/bin/python -m zmovie_platform.project_reset list")"
remaining_count="$(python3 - "$count_json" <<'PY'
import json, sys
print(json.loads(sys.argv[1]).get('count', -1))
PY
)"
[[ "$remaining_count" == "1" ]] || fail "expected exactly one project after reset; found $remaining_count"

chown -R "$SERVICE_USER:$SERVICE_USER" "$MEDIA_ROOT" "$PUBLISH_ROOT" "$EXPORT_ROOT"

if [[ "$service_was_active" -eq 1 ]]; then
  log "starting zmovie and validating health before commit"
  systemctl start zmovie
  healthy=0
  for _ in $(seq 1 30); do
    if curl -fsS "http://127.0.0.1:${ZMOVIE_PORT:-8080}/api/v2/health" >/dev/null 2>&1; then
      healthy=1
      break
    fi
    sleep 1
  done
  [[ "$healthy" -eq 1 ]] || fail "service did not recover after reset"
fi

committed=1
rm -rf -- "$quarantine"
trap - EXIT
log "PASS: old prj_* projects removed and fresh production project created"
printf '[zMovie project reset] new project: %s\n' "$new_project_id"
printf '[zMovie project reset] final video: %s\n' "$new_video"
printf '[zMovie project reset] backup retained: %s\n' "$backup"
