# DBC Windows SMB storage tier

The DBC production host keeps active zMovie runtime data on the Ubuntu local disk and uses Windows SMB as the capacity tier.

## Policy

- Local `/var/lib/zmovie`: SQLite/worker state, active models, render workspace, temp/cache, and current working set.
- SMB `/mnt/zmovie-storage`: source media, completed videos, exports, archives, backups, and copied closeout evidence.
- Never place the SQLite queue/database or an in-progress render workspace directly on SMB.
- A completed artifact must be validated by the production pipeline, copied with `rsync`, and SHA-256 verified before the SMB copy is treated as durable evidence.
- The closeout wrapper refuses to continue when the configured SMB path is not actually a CIFS/SMB mount, preventing an accidental copy into the 300 GB Linux root disk.

## Windows share

Create a dedicated Windows share such as `zmovie` on the HDD storage pool and grant a dedicated service account read/write access. Do not put the SMB password in `/etc/fstab` or the repository.

Ubuntu example credential file `/etc/zmovie/smb.credentials`:

```ini
username=YOUR_WINDOWS_SMB_USER
password=YOUR_WINDOWS_SMB_PASSWORD
domain=WORKGROUP
```

Protect it:

```bash
sudo install -d -m 700 /etc/zmovie
sudo chmod 600 /etc/zmovie/smb.credentials
sudo apt-get update && sudo apt-get install -y cifs-utils rsync
sudo mkdir -p /mnt/zmovie-storage
```

Example `/etc/fstab` entry (replace the server address/share):

```fstab
//WINDOWS-IP/zmovie /mnt/zmovie-storage cifs credentials=/etc/zmovie/smb.credentials,vers=3.1.1,iocharset=utf8,_netdev,nofail,x-systemd.automount,x-systemd.device-timeout=10s,file_mode=0660,dir_mode=0770 0 0
```

Then:

```bash
sudo systemctl daemon-reload
sudo mount /mnt/zmovie-storage
findmnt /mnt/zmovie-storage
```

## Canonical one-click production command

`make production` is the canonical entry point. In `SMB_MODE=auto` it detects a real CIFS/SMB3 mount and automatically switches to the DBC five-gate SMB closeout. If SMB is not mounted it falls back to the local production pipeline. For the DBC production server, use `SMB_MODE=required` so missing Windows storage fails closed.

```bash
git pull --ff-only
make production \
  PROJECT_ID=prj_YOUR_REAL_PROJECT \
  PROVIDER=auto \
  SMB_MODE=required \
  SMB_MOUNT=/mnt/zmovie-storage
```

For controlled reboot recovery evidence:

```bash
make production \
  PROJECT_ID=prj_YOUR_REAL_PROJECT \
  PROVIDER=auto \
  SMB_MODE=required \
  SMB_MOUNT=/mnt/zmovie-storage \
  REBOOT=true
```

The Make target verifies that the configured SMB path is a real `cifs`/`smb3` mount before invoking `scripts/runtime-closeout-smb.sh`. The wrapper performs a write/read/delete probe, checks Linux free space, invokes all five runtime closeout gates, copies the resulting evidence to SMB, and verifies all copied evidence with SHA-256.

Default local-space policy is warning below 60 GB and block below 30 GB. Override with `ZMOVIE_WARN_LOCAL_GB` and `ZMOVIE_MIN_LOCAL_GB` only after capacity planning.

SMB evidence is written below:

```text
/mnt/zmovie-storage/evidence/runtime-closeout/<UTC timestamp>/
```

It includes `SHA256SUMS`, `SMB_VERIFY.log`, `STORAGE.txt`, and `storage-report.json` in addition to the runtime-closeout evidence.
