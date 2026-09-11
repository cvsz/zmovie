# SMB troubleshooting

If `findmnt` does not show `cifs` or `smb3`, confirm the Windows share is online, the VM can reach the Windows host, the credentials file is valid, and the `/etc/fstab` entry uses `_netdev,x-systemd.automount,nofail`. If the write probe fails, verify share and NTFS permissions for the dedicated account. If local free space is below the threshold, archive completed media or expand local capacity before accepting another render. Never lower the threshold merely to bypass a full disk condition.
