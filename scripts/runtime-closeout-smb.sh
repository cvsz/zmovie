#!/usr/bin/env bash
set -Eeuo pipefail

# One-click DBC closeout with Windows SMB storage tier.
# Render/state remain local; validated evidence/exports are copied to SMB and
# checksum-verified before any optional local cleanup.

REPO_DIR="${ZMOVIE_REPO_DIR:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)}"
DATA_DIR="${ZMOVIE_DATA_DIR:-/var/lib/zmovie}"
SMB_MOUNT="${ZMOVIE_SMB_MOUNT:-/mnt/zmovie-storage}"
SMB_REQUIRED="${ZMOVIE_SMB_REQUIRED:-1}"
MIN_LOCAL_GB="${ZMOVIE_MIN_LOCAL_GB:-30}"
WARN_LOCAL_GB="${ZMOVIE_WARN_LOCAL_GB:-60}"
DO_CLEANUP="${ZMOVIE_SMB_CLEANUP_LOCAL:-0}"

usage() {
  cat <<'EOF'
Usage:
  sudo ./scripts/runtime-closeout-smb.sh [runtime-closeout options]

Passes all arguments (for example --project, --provider, --reboot) to
scripts/runtime-closeout.sh.

Environment:
  ZMOVIE_SMB_MOUNT=/mnt/zmovie-storage
  ZMOVIE_SMB_REQUIRED=1
  ZMOVIE_MIN_LOCAL_GB=30
  ZMOVIE_WARN_LOCAL_GB=60
  ZMOVIE_SMB_CLEANUP_LOCAL=0

Storage policy:
  Linux local disk = hot state/models/render/temp.
  Windows SMB = source/video/export/archive/backup/evidence.
  SQLite/active render/temp are never moved to SMB by this script.
EOF
}

[[ ${EUID} -eq 0 ]] || { echo "ERROR: run with sudo/root" >&2; exit 2; }
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then usage; exit 0; fi

for c in findmnt df sha256sum rsync python3; do
  command -v "$c" >/dev/null || { echo "ERROR: required command missing: $c" >&2; exit 2; }
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PRE="$DATA_DIR/evidence/smb-preflight/$STAMP"
mkdir -p "$PRE"

# SMB must already be mounted by systemd/fstab; never accept a plain local
# directory at the SMB path because that could silently fill the Linux disk.
if ! findmnt -T "$SMB_MOUNT" -n -o FSTYPE,SOURCE,TARGET >"$PRE/findmnt.txt" 2>&1; then
  echo "BLOCKED: SMB mount is unavailable at $SMB_MOUNT" >&2
  [[ "$SMB_REQUIRED" == "1" ]] && exit 20
else
  fstype="$(awk '{print $1}' "$PRE/findmnt.txt")"
  case "$fstype" in cifs|smb3) ;; *) echo "BLOCKED: $SMB_MOUNT is mounted as $fstype, expected cifs/smb3" >&2; exit 21;; esac
fi

# Read/write/delete probe and local-space guard.
probe="$SMB_MOUNT/.zmovie-write-probe-$STAMP"
printf 'zmovie-smb-probe %s\n' "$STAMP" > "$probe"
sync "$probe" 2>/dev/null || true
[[ -s "$probe" ]] || { echo "BLOCKED: SMB write/read probe failed" >&2; exit 22; }
rm -f "$probe"

avail_kb="$(df -Pk "$DATA_DIR" | awk 'NR==2{print $4}')"
avail_gb=$((avail_kb / 1024 / 1024))
printf 'local_available_gb=%s\n' "$avail_gb" > "$PRE/storage.txt"
df -hT "$DATA_DIR" "$SMB_MOUNT" >> "$PRE/storage.txt"
if (( avail_gb < MIN_LOCAL_GB )); then
  echo "BLOCKED: only ${avail_gb}GB local free; minimum is ${MIN_LOCAL_GB}GB" >&2
  exit 23
elif (( avail_gb < WARN_LOCAL_GB )); then
  echo "WARNING: local free space ${avail_gb}GB is below ${WARN_LOCAL_GB}GB"
fi

# Execute the existing five evidence gates. Its reports remain local until
# successfully archived and verified below.
"$REPO_DIR/scripts/runtime-closeout.sh" "$@"
rc=$?

latest="$(find "$DATA_DIR/evidence/runtime-closeout" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)"
[[ -n "$latest" && -d "$latest" ]] || { echo "ERROR: runtime closeout report not found" >&2; exit 24; }

archive="$SMB_MOUNT/evidence/runtime-closeout/$(basename "$latest")"
mkdir -p "$archive"
rsync -a --partial --delay-updates "$latest/" "$archive/"

# Verify every regular evidence file byte-for-byte using SHA-256.
(
  cd "$latest"
  find . -type f -print0 | sort -z | xargs -0 sha256sum
) > "$PRE/local.sha256"
(
  cd "$archive"
  sha256sum -c "$PRE/local.sha256"
) > "$PRE/smb-verify.log"
cp "$PRE/local.sha256" "$archive/SHA256SUMS"
cp "$PRE/smb-verify.log" "$archive/SMB_VERIFY.log"
cp "$PRE/storage.txt" "$archive/STORAGE.txt"

python3 - "$latest/report.json" "$archive/storage-report.json" "$SMB_MOUNT" "$archive" "$avail_gb" <<'PY'
import json, pathlib, sys
src,out,mount,archive,free=sys.argv[1:]
data={}
try: data=json.loads(pathlib.Path(src).read_text())
except Exception: pass
data['storage_tier']={
 'local_hot_root':'/var/lib/zmovie',
 'smb_mount':mount,
 'smb_archive':archive,
 'smb_verified':True,
 'checksum':'sha256',
 'local_free_gb_before_closeout':int(free),
 'policy':'render/state/models/temp local; validated exports/evidence/archive/backup on SMB'
}
pathlib.Path(out).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
PY

if [[ "$DO_CLEANUP" == "1" ]]; then
  # Only evidence copy is eligible here. Active state/models/render/temp are
  # deliberately excluded; production cleanup should be project-aware.
  echo "cleanup_requested=true; no active runtime data removed" > "$archive/CLEANUP.txt"
fi

echo "SMB closeout PASS"
echo "Local report: $latest"
echo "SMB verified archive: $archive"
exit "$rc"
