# zMovie operations guide

This guide covers the safe lifecycle of a native or Docker deployment. It
separates service health, durable worker state, renderer readiness, production
media validation, and external publication evidence.

## Native installation and upgrade

From a reviewed repository checkout, the installer provisions the hardened web
service, dedicated production worker, watchdog/backup timers, runtime
dependencies, FFmpeg/ffprobe, Playwright when configured, persistent data, and
the operator CLI. The public one-command installer is documented in the
[README](../README.md#one-command-native-install).

For an existing native installation, check the durable upgrade gate first:

```bash
sudo zmovie-ctl upgrade-readiness
sudo bash /opt/zmovie/install.sh upgrade
sudo systemctl status zmovie
sudo systemctl status zmovie-worker
sudo systemctl status zmovie-watchdog.timer
sudo systemctl status zmovie-backup.timer
sudo zmovie-ctl doctor
```

The upgrade path creates a consistent SQLite backup and preserves persistent
configuration, queue state, media, exports, publication packages, model storage
and evidence. It refuses an unsafe upgrade while a worker lease is executing or
an external publication transition requires reconciliation.

## Health, logs, and control

```bash
sudo zmovie-ctl status
sudo zmovie-ctl health
sudo zmovie-ctl doctor
sudo zmovie-ctl worker-status
sudo zmovie-ctl watchdog-status
sudo zmovie-ctl backup-status
sudo journalctl -u zmovie -f
sudo zmovie-ctl worker-logs 200
```

The public health response is intentionally redacted. Use the operator CLI and
service logs for detailed diagnostics, then redact host-specific information
before sharing. The [Makefile and CLI guide](MAKEFILE_CLI_CONTROL.md) contains
the broader command catalog.

## Durable production worker

Long AI execution is not owned by uvicorn. Production requests create durable
SQLite jobs and return; `zmovie-worker.service` claims the jobs, heartbeats its
lease, retries bounded failures and reconciles stale work after restart.

```bash
sudo zmovie-ctl worker-status
sudo zmovie-ctl worker-jobs
sudo zmovie-ctl worker-job wrk_EXAMPLE
sudo zmovie-ctl worker-recover --dry-run
sudo zmovie-ctl worker-recover --apply
sudo zmovie-ctl worker-pause
sudo zmovie-ctl worker-resume
sudo zmovie-ctl worker-restart
```

Pause stops new claims; it does not terminate a currently running renderer.
Recovery of a stale ComfyUI render uses the checkpointed remote `prompt_id`
before any new submission. External publishing ambiguity is fail-closed and
must be reconciled instead of retried.

## Watchdog

`zmovie-watchdog.timer` runs periodically. It checks API liveness, SQLite,
data-root writability, free disk, web service state and worker state when active
work requires the worker. Renderer/model readiness is informational and never
causes restart loops.

```bash
sudo zmovie-ctl watchdog-status
sudo zmovie-ctl watchdog-run
systemctl list-timers zmovie-watchdog.timer
```

The systemd watchdog invocation may perform rate-limited repair of a
demonstrably unhealthy web service or required worker. Manual status commands
do not weaken renderer or publication safety gates.

## Docker operations

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=100
docker compose down
```

Keep the persistent `zmovie-data` volume when stopping a service. Do not use a
purge or volume deletion command without a verified database backup and an
explicit operator decision.

## Renderer readiness

Check providers and strict readiness before production:

```bash
sudo zmovie-ctl providers
sudo zmovie-ctl doctor
sudo zmovie-ctl renderer-doctor
sudo zmovie-ctl vulkan-status
sudo zmovie-ctl sdcpp-status
sudo zmovie-ctl readiness prj_EXAMPLE
```

The native web service remains isolated from `/dev/dri`. GPU/Vulkan access
belongs to the worker. The bundled ComfyUI smoke workflow proves API
queue/history/output integration, not accelerated AI-video throughput.
stable-diffusion.cpp CPU/Vulkan can be a real provider only when compatible,
operator-supplied model files generate valid video media.

## Production pipeline

The guarded sequence is:

```text
content/storyboard
  -> durable queue
  -> render every shot
  -> validate real media
  -> assemble
  -> validate final movie
  -> prepare package
  -> export
  -> approval_required
  -> human exact-package approval
  -> fail-closed preflight
  -> one external submission attempt
  -> public URL confirmation
```

Use a real configured provider for production. The mock provider is limited to
dry runs and tests. A failed shot, invalid video, missing model, or unavailable
renderer stops the pipeline before assembly or publication. Product Studio
creates a normal project and hands it to this same production path.

## Bilibili safety sequence

```bash
sudo zmovie-ctl bili-session
sudo zmovie-ctl bili-status pub_EXAMPLE
sudo zmovie-ctl bili-approve pub_EXAMPLE APPROVE
sudo zmovie-ctl bili-publish pub_EXAMPLE CONFIRM-PUBLISH
```

The final command performs a live session check and one guarded submission
attempt. `submitted` is not public publication. Confirm the concrete public URL
with the documented confirmation command and record `remote_confirmation=true`.
See the [real-publication runbook](BILIBILI_REAL_PUBLISH_RUNBOOK.md).

## Backup and restore

A verified SQLite backup timer runs daily by default. Backups use SQLite's
online backup API, validate `PRAGMA quick_check` and `PRAGMA foreign_key_check`,
and atomically promote only a successful candidate. At least 14 recent backups
are retained by default.

```bash
sudo zmovie-ctl backup
sudo zmovie-ctl backups
sudo zmovie-ctl backup-status
systemctl list-timers zmovie-backup.timer
```

Restore only after identifying the exact backup and target data root. Stop the
services, preserve the current data for rollback, validate the restored
database and media paths, and run health/doctor checks before resuming
operations. See [Backup and recovery](BACKUP_AND_RECOVERY.md).

## Runtime evidence

```bash
sudo zmovie-ctl sdcpp-evidence
```

This records factual runtime inspection only. Real-model verification requires
an operator-supplied video-capable model to generate an actual FFprobe-valid
video. See [Runtime evidence](RUNTIME_EVIDENCE.md).

## Operational safety

Never publish, delete projects, purge volumes, expose renderer APIs, or replace
browser state as a side effect of a health check. Keep authentication enabled,
use TLS or a controlled tunnel for public access, retain web/worker privilege
separation, and retain the human approval gate for external publication.
