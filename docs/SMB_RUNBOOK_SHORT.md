# SMB one-click short runbook

```bash
sudo install -d -m 700 /etc/zmovie
sudo install -m 600 /dev/null /etc/zmovie/smb.credentials
sudoedit /etc/zmovie/smb.credentials
sudo ./scripts/install-smb-storage.sh //WINDOWS-IP/zmovie /mnt/zmovie-storage
sudo ./scripts/smb-storage-doctor.sh
make production PROJECT_ID=prj_REAL PROVIDER=auto SMB_MODE=required
```

Add `REBOOT=true` only when a controlled reboot is acceptable. `make production` automatically uses the SMB-enabled five-gate closeout when the configured mount is a real CIFS/SMB3 filesystem, then checksum-verifies the copied evidence on Windows SMB.
