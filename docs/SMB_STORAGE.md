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

Ubuntu example credential file `/root/.smb-zmovie`:

```ini
username=YOUR_WINDOWS_SMB_USER
password=YOUR_WINDOWS_SMB_PASSWORD
domain=WORKGROUP
```

Protect it:

```bash
sudo chmod 600 /root/.smb-zmovie
sudo apt-get update && sudo apt-get install -y cifs-utils rsync
sudo mkdir -p /mnt/zmovie-storage
```

Example `/etc/fstab` entry (replace the server address/share):

```fstab
//WINDOWS-IP/zmovie /mnt/zmovie-storage cifs credentials=/root/.smb-zmovie,vers=3.1.1,iocharset=utf8,_netdev,nofail,x-systemd.automount,x-systemd.device-timeout=10s,file_mode=0660,dir_mode=0770 0 0
```

Then:

```bash
sudo systemctl daemon-reload
sudo mount /mnt/zmovie-storage
findmnt /mnt/zmovie-storage
```

## One-click five-gate closeout + SMB evidence

```bash
cd ~/zmovie
git pull --ff-only
sudo ZMOVIE_SMB_MOUNT=/mnt/zmovie-storage \
  ./scripts/runtime-closeout-smb.sh \
  --project prj_YOUR_REAL_PROJECT \
  --provider auto
```

For controlled reboot recovery evidence:

```bash
sudo ZMOVIE_SMB_MOUNT=/mnt/zmovie-storage \
  ./scripts/runtime-closeout-smb.sh \
  --project prj_YOUR_REAL_PROJECT \
  --provider auto \
  --reboot
```

The wrapper first verifies that the target is a real `cifs`/`smb3` mount, performs a write/read/delete probe, checks Linux free space, invokes all five existing runtime closeout gates, copies the resulting evidence to SMB, and verifies all copied evidence with SHA-256.

Default local-space policy is warning below 60 GB and block below 30 GB. Override with `ZMOVIE_WARN_LOCAL_GB` and `ZMOVIE_MIN_LOCAL_GB` only after capacity planning.

SMB evidence is written below:

```text
/mnt/zmovie-storage/evidence/runtime-closeout/<UTC timestamp>/
```

It includes `SHA256SUMS`, `SMB_VERIFY.log`, `STORAGE.txt`, and `storage-report.json` in addition to the runtime-closeout evidence.
