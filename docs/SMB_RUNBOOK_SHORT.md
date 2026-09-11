# SMB one-click short runbook

```bash
sudo install -m 600 /dev/null /root/.smb-zmovie
sudoedit /root/.smb-zmovie
sudo ./scripts/install-smb-storage.sh //WINDOWS-IP/zmovie /mnt/zmovie-storage
sudo ./scripts/smb-storage-doctor.sh
sudo ./scripts/runtime-closeout-smb.sh --project prj_REAL --provider auto
```

Add `--reboot` only when a controlled reboot is acceptable. The last command runs the existing five closeout gates and then checksum-verifies the copied evidence on Windows SMB.
