# SMB security notes

Use SMB 3.1.1 where supported and a dedicated least-privilege Windows service account for the zMovie share. Keep credentials only in the root-readable credentials file on the DBC Ubuntu host (`chmod 600`); never commit credentials or place them directly in `/etc/fstab`. Restrict Windows firewall access to the DBC/VM network as appropriate. The runtime closeout verifies the mounted filesystem type before writing so an unavailable share cannot silently redirect archive writes onto the Linux root disk.
