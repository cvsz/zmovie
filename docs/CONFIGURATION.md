# zMovie configuration

Configuration is supplied through the environment and deployment-specific
files. Keep credentials in operator-controlled secret storage. This guide names
variables and safe defaults; it never contains their values.

## Core application settings

| Setting | Role | Safety expectation |
| --- | --- | --- |
| `ZMOVIE_DB_PATH` | SQLite database and durable worker-queue location. | Keep it under the managed data root and back it up before destructive work. |
| `ZMOVIE_DATA_DIR` | Runtime data root. | Keep media, exports, evidence, publication packages, and browser state out of Git. |
| `ZMOVIE_SECRET_KEY` | Persistent token/signing secret. | Generate and provide it through deployment secret storage. |
| `ZMOVIE_AUTH_ENABLED` | Authentication policy switch. | Keep enabled for production exposure. |
| `ZMOVIE_ENABLE_DOCS` | Explicit API documentation switch. | Leave disabled on public deployments. |
| `ZMOVIE_HOST` / `ZMOVIE_PORT` | Local bind and HTTP port. | Bind privately or put authenticated TLS ingress in front. |

The native installer preserves persistent configuration during upgrades. Docker
uses the Compose environment and persistent `zmovie-data` volume. Consult the
[native deployment notes](../zmovie_platform/README_DEPLOYMENT.md) and
[Docker notes](../zmovie_platform/README_DOCKER.md) for surface-specific paths.

## Durable worker and operations

Native production installs separate the hardened web service from the durable
renderer worker. These settings tune that runtime without placing credentials
inside queue payloads:

| Setting | Default | Role |
| --- | --- | --- |
| `ZMOVIE_WORKER_LEASE_SECONDS` | `120` | Worker claim lease; renewed by heartbeat while long work executes. |
| `ZMOVIE_WORKER_POLL_SECONDS` | `2` | Idle queue polling interval. |
| `ZMOVIE_WORKER_RETRY_DELAY` | `30` | Delay before a retryable failed job is eligible again. |
| `ZMOVIE_BACKUP_DIR` | `/var/backups/zmovie` native | Verified SQLite backup directory. |
| `ZMOVIE_BACKUP_RETENTION` | at least `14` | Number of recent verified backups retained. |
| `ZMOVIE_EVIDENCE_ROOT` | `/var/lib/zmovie/evidence` native | Factual runtime evidence directory. |
| `ZMOVIE_WATCHDOG_RESTART_COOLDOWN` | `600` | Minimum interval between automatic restart attempts for a component. |

The queue explicitly rejects credential-like fields such as password, token,
secret, cookie, authorization and browser-state values. Keep provider tokens in
the protected environment file instead.

Production model weights should live below `/var/lib/zmovie/models` on a native
install so the worker remains compatible with `ProtectHome=true`.

## Renderer settings

### ComfyUI

Use `ZMOVIE_COMFYUI_URL` for the API endpoint and the configured workflow path
and role settings described in [ComfyUI workflow integration](../workflows/comfyui/README.md).
Local Docker containers use the host gateway where required. Do not expose an
unauthenticated ComfyUI API to the public internet.

The provider checkpoints a remote `prompt_id` and `client_id` into local render
job metadata. Those identifiers are execution metadata, not credentials. On
recovery zMovie queries the existing history before deciding whether new work
is needed.

### stable-diffusion.cpp

The provider settings include:

```text
ZMOVIE_SDCPP_CLI
ZMOVIE_SDCPP_BACKEND
ZMOVIE_SDCPP_VIDEO_ENABLED
ZMOVIE_SDCPP_MODEL
ZMOVIE_SDCPP_DIFFUSION_MODEL
ZMOVIE_SDCPP_HIGH_NOISE_DIFFUSION_MODEL
ZMOVIE_SDCPP_VAE
ZMOVIE_SDCPP_AUDIO_VAE
ZMOVIE_SDCPP_T5XXL
ZMOVIE_SDCPP_LLM
ZMOVIE_SDCPP_CLIP_VISION
ZMOVIE_SDCPP_EMBEDDINGS_CONNECTORS
ZMOVIE_SDCPP_PARAMS_BACKEND
ZMOVIE_SDCPP_MAX_VRAM
ZMOVIE_SDCPP_AUTO_FIT
ZMOVIE_SDCPP_EXTRA_ARGS_JSON
ZMOVIE_SDCPP_FPS
ZMOVIE_SDCPP_FRAME_MULTIPLE
ZMOVIE_SDCPP_FRAME_OFFSET
ZMOVIE_SDCPP_WIDTH
ZMOVIE_SDCPP_HEIGHT
ZMOVIE_SDCPP_OUTPUT_FORMAT
ZMOVIE_SDCPP_SEED
ZMOVIE_SDCPP_TIMEOUT
```

At least one model path and explicit video enablement are required for strict
video readiness. Extra arguments cannot override zMovie-controlled prompt,
output, mode, backend, frame, dimensions, seed, parameter-backend, or VRAM
flags. CPU can be a real backend; CUDA is not mandatory. A backend is not
real-model verified until it produces real FFprobe-valid video. Use the
[stable-diffusion.cpp runbook](SDCPP_LOCAL_RENDERER.md).

## Publication settings

Treat Bilibili Playwright browser state as a credential. Store it only in the
operator-managed runtime data root with restrictive permissions. The publisher
does not accept Google passwords or 2FA secrets. Keep automatic publication
disabled by default and require the documented approval and confirmation tokens
for any real external submission.

Bilibili state is deliberately not embedded in worker queue payload JSON. An
ambiguous external transition blocks unsafe retries and can also make the
upgrade-readiness gate fail closed until reconciled.

## Precedence and validation

The effective value comes from the deployment environment and its explicitly
loaded configuration, with application defaults used only when documented.
Inspect redacted configuration through the operator CLI rather than printing
environment files. Validate changes with:

```bash
sudo zmovie-ctl health
sudo zmovie-ctl doctor
sudo zmovie-ctl worker-status
sudo zmovie-ctl watchdog-status
sudo zmovie-ctl backup-status
sudo zmovie-ctl upgrade-readiness
docker compose config --quiet
```

Never test a secret by echoing it. Record variable names and pass/fail results,
not credential values.
