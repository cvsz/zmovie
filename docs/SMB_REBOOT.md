# SMB and reboot closeout

A post-boot archival resume unit for the SMB wrapper has not yet been implemented or verified. The wrapper fails closed on `--reboot`, since a reboot terminates its parent process before the SMB archive/checksum step.

For now, complete the non-reboot SMB closeout, archive and checksum-verify its evidence, then perform a separately controlled and evidenced reboot recovery drill. After reboot, verify `findmnt -T /mnt/zmovie-storage -n -o FSTYPE` returns `cifs` or `smb3`, run the SMB doctor, and archive the separate reboot evidence. A future change can add a systemd resume service with a tested archive-only continuation.
