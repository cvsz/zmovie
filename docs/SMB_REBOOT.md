# SMB and reboot closeout

The Windows share must be reachable again after Ubuntu reboots. Configure `_netdev,nofail,x-systemd.automount` so boot is not blocked by temporary SMB unavailability. The SMB wrapper performs its own mount/type and write checks before starting. For reboot-level evidence, run the wrapper with `--reboot`; the underlying runtime closeout resumes once after boot. If SMB is not available when the wrapper is initially invoked, it fails closed rather than storing evidence in the local mount directory.
