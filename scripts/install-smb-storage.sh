#!/usr/bin/env bash
set -Eeuo pipefail

# Installs the Linux side of the Windows SMB storage tier without embedding credentials.
# Usage: sudo ./scripts/install-smb-storage.sh //WINDOWS-IP/zmovie /mnt/zmovie-storage

SHARE="${1:-}"
MOUNT="${2:-/mnt/zmovie-storage}"
CRED="${ZMOVIE_SMB_CREDENTIALS:-/root/.smb-zmovie}"
[[ ${EUID} -eq 0 ]] || { echo "ERROR: run as root" >&2; exit 2; }
[[ "$SHARE" == //*/* ]] || { echo "Usage: sudo $0 //WINDOWS-IP/zmovie [/mnt/zmovie-storage]" >&2; exit 2; }
[[ -f "$CRED" ]] || { echo "ERROR: create $CRED first (username/password/domain) and chmod 600" >&2; exit 3; }
chmod 600 "$CRED"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y cifs-utils rsync
mkdir -p "$MOUNT"
entry="$SHARE $MOUNT cifs credentials=$CRED,vers=3.1.1,iocharset=utf8,_netdev,nofail,x-systemd.automount,x-systemd.device-timeout=10s,file_mode=0660,dir_mode=0770 0 0"
if ! grep -Fqs "$SHARE $MOUNT cifs " /etc/fstab; then
  printf '%s\n' "$entry" >> /etc/fstab
fi
systemctl daemon-reload
mount "$MOUNT" || true
findmnt -T "$MOUNT" -n -o SOURCE,FSTYPE,TARGET
probe="$MOUNT/.zmovie-install-probe-$$"
printf 'ok\n' > "$probe"
grep -qx ok "$probe"
rm -f "$probe"
echo "SMB storage ready: $MOUNT"
