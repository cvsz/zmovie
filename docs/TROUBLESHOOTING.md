# zMovie troubleshooting

Diagnose from the first failing boundary and record the exact command and
observed output. Do not guess from a green unit test or a stale status page.

## Fast triage

Run the least-invasive checks first:

```bash
sudo zmovie-ctl status
sudo zmovie-ctl health
sudo zmovie-ctl worker-status
sudo zmovie-ctl watchdog-status
sudo zmovie-ctl backup-status
sudo zmovie-ctl doctor
sudo journalctl -u zmovie --no-pager -n 100
sudo journalctl -u zmovie-worker --no-pager -n 100
```

For Docker, use `docker compose config --quiet`, `docker compose ps`, and
`docker compose logs --tail=100`. Keep host and container network paths
separate when testing a renderer or database.

## Common symptoms

| Symptom | Evidence to collect | Likely boundary |
| --- | --- | --- |
| Web service is inactive | systemd status, API health and recent web journal lines. | Installer, dependency, configuration, or startup failure. |
| Worker is inactive with queued work | `worker-status`, worker journal and systemd status. | Worker unit/runtime failure. |
| Durable job stays claimed/running after worker loss | worker job, heartbeat and lease timestamps; run `worker-recover --dry-run`. | Stale worker lease requiring safe recovery. |
| Job enters `retry_wait` | worker job attempts, safe error type/message, renderer state. | Retryable render/provider failure. |
| Job enters `recovery_required` | exact worker/publish state and external platform state. | Ambiguous external transition; never blind retry. |
| Health is reachable but renderer not ready | Redacted health, doctor, `renderer-doctor`, `vulkan-status`, `sdcpp-status`. | Renderer/model/device prerequisite, not necessarily API failure. |
| `/dev/dri` exists but worker cannot use it | `id zmovie`, render/video groups, `sudo -u zmovie vulkaninfo --summary`, `sudo -u zmovie sd-cli --list-devices`. | Device node permissions or worker supplementary groups. |
| Studio loads but API action fails | HTTP status, route, auth state, ownership and server log. | Authentication, ownership, request validation, or route contract. |
| ComfyUI work appears duplicated | render-job metadata `comfyui_prompt_id`, worker logs and `/history/{prompt_id}` on the private renderer. | Remote checkpoint/reconciliation boundary. Do not submit again until reconciled. |
| stable-diffusion.cpp is installed but not production-ready | `sdcpp-status`, model path checks, video enablement and ffprobe result. | Model bundle or media-readiness gate. |
| Render completes but assembly stops | Per-shot media metadata and ffprobe facts. | Managed-root, video stream, duration, dimension, or codec validation. |
| Backup timer ran but no usable backup exists | `backup-status`, timer/service journal, target permissions, quick/FK checks. | Backup storage or integrity failure. |
| Watchdog reports unhealthy with no model | Confirm whether API/database/service failed; model readiness alone is informational. | Health versus renderer-readiness confusion. |
| Upgrade is refused | `upgrade-readiness`, active worker jobs and ambiguous publish state. | Drain/recovery gate is protecting in-flight work. |
| Bilibili job stays submitted | Job state, public URL, and remote confirmation metadata. | External Creator Center publication confirmation is incomplete. |
| Tests fail importing an optional module | Python executable, installed requirements, isolated environment. | Dependency environment rather than a source regression. |
| `compileall` cannot write bytecode | Cache owner/mode and current user. | Host-generated root-owned cache; use an isolated bytecode prefix. |

## Durable worker recovery

Inspect before mutating:

```bash
sudo zmovie-ctl worker-status
sudo zmovie-ctl worker-jobs
sudo zmovie-ctl worker-recover --dry-run
```

Only after reviewing stale leases:

```bash
sudo zmovie-ctl worker-recover --apply
```

A stale local render may be retried within its bounded retry budget. A
checkpointed ComfyUI render must reconcile its existing remote `prompt_id`
first. Any job that may have crossed an external publication boundary is not a
normal renderer retry and must remain fail-closed until external state is
known.

## Dependency environment

Use the declared requirements in an isolated environment. The system Python may
not contain optional modules such as `edge_tts`, and a repository cache created
by a privileged command may be unwritable by the developer account.

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m unittest discover -s tests -v
```

If the repository contains root-owned caches, do not recursively change broad
ownership as a troubleshooting shortcut. Run the relevant check with
`PYTHONPYCACHEPREFIX` pointing to a temporary directory outside the repository
and document the environment condition.

## Renderer and network boundaries

For ComfyUI, verify the renderer from the same network namespace as zMovie. A
host request succeeding does not prove that a container can resolve or reach
the same address. Do not fix stale container routing by pinning an ephemeral
container IP or exposing a private renderer port.

For the native worker, run device checks in the service-user context where
possible. `renderer-doctor` reports the current identity and read/write access
to discovered render nodes. The web service intentionally keeps
`PrivateDevices=true`; do not weaken it to fix worker Vulkan access.

For public Cloudflare or reverse-proxy paths, test the local service, ingress,
and public endpoint separately. A transient public request should be retried
within a bounded window before diagnosing the tunnel, but repeated HTTP success
does not prove every application route is secure.

## Backup and timer recovery

```bash
systemctl list-timers zmovie-backup.timer zmovie-watchdog.timer
sudo systemctl status zmovie-backup.service
sudo systemctl status zmovie-watchdog.service
sudo zmovie-ctl backups
```

A failed backup candidate is not promoted into the verified set. Do not delete
the newest verified backup while investigating retention. A watchdog repair is
rate-limited and only targets demonstrably unhealthy service components; it
must not be used as a renderer/model readiness loop.

## Recovery boundaries

Back up the database before reset or restore. Keep the current data available
until the restored service passes health, ownership, media, worker-queue and
publication-job checks. Never use a production purge command as a diagnostic
step. Before upgrades use `sudo zmovie-ctl upgrade-readiness` and resolve active
leases or ambiguous external transitions rather than killing them.

For a suspected vulnerability, stop public disclosure and follow
[SECURITY.md](../SECURITY.md). For normal support, use [SUPPORT.md](../SUPPORT.md)
after redacting logs and environment details.
