#!/usr/bin/env bash
set -Eeuo pipefail
MOUNT="${ZMOVIE_SMB_MOUNT:-/mnt/zmovie-storage}"
DATA="${ZMOVIE_DATA_DIR:-/var/lib/zmovie}"
findmnt -T "$MOUNT" -o SOURCE,FSTYPE,SIZE,USED,AVAIL,TARGET
fstype="$(findmnt -T "$MOUNT" -n -o FSTYPE)"
[[ "$fstype" == "cifs" || "$fstype" == "smb3" ]] || { echo "FAIL: expected cifs/smb3" >&2; exit 2; }
probe="$MOUNT/.zmovie-doctor-$$"
printf 'zmovie\n' > "$probe"
grep -qx zmovie "$probe"
rm -f "$probe"
echo "Local hot storage:"
df -hT "$DATA"
echo "SMB storage: PASS"
