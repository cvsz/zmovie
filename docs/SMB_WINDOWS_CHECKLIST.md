# Windows SMB checklist

- Create a dedicated `zmovie` share on the Windows HDD storage area.
- Create/use a dedicated least-privilege SMB service account.
- Grant share and NTFS modify permissions only as needed.
- Prefer SMB 3.x and restrict Windows Firewall/network access appropriately.
- Keep Windows credentials out of Git.
- Confirm the Ubuntu VM can reach TCP 445 on the Windows host.
- Confirm `scripts/smb-storage-doctor.sh` passes before production closeout.
