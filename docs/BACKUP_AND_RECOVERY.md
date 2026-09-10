# Backup and recovery

The native production installation provisions `zmovie-backup.service` and `zmovie-backup.timer`. The timer runs daily at approximately 03:15 with `Persistent=true` and up to five minutes randomized delay.

Backups use SQLite's online backup API. A candidate backup is written to a temporary file, validated with `PRAGMA quick_check` and `PRAGMA foreign_key_check`, then atomically moved into the backup set. A failed candidate never replaces a verified backup. Retention defaults to at least 14 recent backups.

## Commands

```bash
sudo zmovie-ctl backup
sudo zmovie-ctl backups
sudo zmovie-ctl backup-status
systemctl status zmovie-backup.timer
```

## Worker recovery

Durable production jobs survive web/worker restarts because their queue state is stored in the same persistent SQLite database. Claimed/running jobs use leases and heartbeats. On worker startup stale local work can be retried within its bounded retry budget. ComfyUI render jobs checkpoint the remote prompt identity and reconcile history before any new submission. Ambiguous external publication state must be reconciled manually and is never blindly retried.

## Upgrade safety

Run:

```bash
sudo zmovie-ctl upgrade-readiness
```

before an upgrade. The gate refuses an upgrade while a worker lease is actively executing or a durable job is in `recovery_required`. Queued work remains safe because it has not been claimed and persists in SQLite.

A restore drill is runtime evidence and must be performed on a controlled host. CI validates backup creation/integrity logic but does not prove a production restore.
