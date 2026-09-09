# zMovie operations guide

This guide covers the safe lifecycle of a native or Docker deployment. It
separates service health, renderer readiness, production media validation, and
external publication evidence.

## Native installation and upgrade

From a reviewed repository checkout, the installer provisions the service,
runtime dependencies, FFmpeg/ffprobe, Playwright when configured, persistent
data, and the operator CLI. The public one-command installer is documented in
the [README](../README.md#one-command-native-install).

For an existing native installation:

```bash
sudo bash /opt/zmovie/install.sh upgrade
sudo systemctl status zmovie
sudo bash /opt/zmovie/scripts/doctor.sh
```

The upgrade path creates a consistent SQLite backup and preserves persistent
configuration and data. Review the output and service state before declaring
the upgrade successful.

## Health, logs, and control

```bash
sudo zmovie-ctl status
sudo zmovie-ctl health
sudo zmovie-ctl doctor
sudo journalctl -u zmovie -f
```

The public health response is intentionally redacted. Use the operator CLI and
service logs for detailed paths and diagnostics, then redact them before
sharing. The [Makefile and CLI guide](MAKEFILE_CLI_CONTROL.md) contains the
complete command catalog.

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
sudo zmovie-ctl sdcpp-status
sudo zmovie-ctl readiness prj_EXAMPLE
```

The bundled ComfyUI smoke workflow proves API queue/history/output integration,
not accelerated AI-video throughput. stable-diffusion.cpp CPU/Vulkan is a
functional fallback whose production status still depends on compatible,
operator-supplied model files and valid output media.

## Production pipeline

The guarded sequence is:

```text
content/storyboard -> render every shot -> validate media -> assemble -> validate final movie
  -> prepare package -> human review/approval -> fail-closed preflight -> external submission
  -> public URL confirmation
```

Use a real configured provider for production. The mock provider is limited to
dry runs and tests. A failed shot, invalid video, missing model, or unavailable
renderer stops the pipeline before assembly or publication.

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

Use the native backup command before upgrades, resets, or other operations that
can alter project state:

```bash
sudo zmovie-ctl backup
```

Restore only after identifying the exact backup and target data root. Stop the
service, preserve the current data for rollback, validate the restored database
and media paths, and run health/doctor checks before resuming operations. See
[backup](../zmovie_platform/README_BACKUP.md) and
[restore](../zmovie_platform/README_RESTORE.md) for implementation details.

## Operational safety

Never publish, delete projects, purge volumes, expose renderer APIs, or replace
browser state as a side effect of a health check. Keep authentication enabled,
use TLS or a controlled tunnel for public access, and retain the human approval
gate for external publication.
