# Runtime inputs

Required operator inputs are the Windows SMB server/share, a dedicated SMB account stored in `/etc/zmovie/smb.credentials`, and a real zMovie project ID for Gate 5. Provider may remain `auto`. No credential value belongs in Git.

For the DBC production path, use:

```bash
make production PROJECT_ID=prj_REAL PROVIDER=auto SMB_MODE=required
```

Optional controls:

- `SMB_MOUNT=/mnt/zmovie-storage` selects the mounted Windows share.
- `SMB_MODE=auto|required|off` controls whether SMB is auto-detected, mandatory, or disabled.
- `REBOOT=true` requests the one-time reboot recovery evidence path.
