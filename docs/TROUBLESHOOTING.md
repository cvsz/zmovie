# zMovie troubleshooting

Diagnose from the first failing boundary and record the exact command and
observed output. Do not guess from a green unit test or a stale status page.

## Fast triage

Run the least-invasive checks first:

```bash
sudo zmovie-ctl status
sudo zmovie-ctl health
sudo zmovie-ctl doctor
sudo journalctl -u zmovie --no-pager -n 100
```

For Docker, use `docker compose config --quiet`, `docker compose ps`, and
`docker compose logs --tail=100`. Keep host and container network paths
separate when testing a renderer or database.

## Common symptoms

| Symptom | Evidence to collect | Likely boundary |
| --- | --- | --- |
| Service is inactive | systemd status and recent journal lines. | Installer, dependency, configuration, or startup failure. |
| Health is reachable but not ready | Redacted health and doctor output. | Renderer/model/media prerequisite, not necessarily API failure. |
| Studio loads but API action fails | HTTP status, route, auth state, and server log. | Authentication, ownership, request validation, or route contract. |
| ComfyUI smoke fails | Renderer URL, `/system_stats`, workflow JSON validation, and queue/history response. | Network boundary, missing node type, or renderer configuration. |
| stable-diffusion.cpp is installed but not production-ready | `sdcpp-status`, model path checks, video enablement, and ffprobe result. | Model bundle or media-readiness gate. |
| Render completes but assembly stops | Per-shot media path and ffprobe metadata. | Managed-root, video stream, duration, dimension, or codec validation. |
| Bilibili job stays submitted | Job state, public URL, and remote confirmation metadata. | External Creator Center publication confirmation is incomplete. |
| Tests fail importing an optional module | Python executable, installed requirements, and isolated environment state. | Dependency environment rather than a source regression. |
| `compileall` cannot write bytecode | Cache owner/mode and current user. | Host-generated root-owned cache; use an isolated bytecode prefix. |

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

For public Cloudflare or reverse-proxy paths, test the local service, ingress,
and public endpoint separately. A transient public request should be retried
within a bounded window before diagnosing the tunnel, but repeated HTTP success
does not prove every application route is secure.

## Recovery boundaries

Back up the database before reset or restore. Keep the current data available
until the restored service passes health, ownership, media, and publication-job
checks. Never use a production purge command as a diagnostic step.

For a suspected vulnerability, stop public disclosure and follow
[SECURITY.md](../SECURITY.md). For normal support, use [SUPPORT.md](../SUPPORT.md)
after redacting logs and environment details.
