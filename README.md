# zMovie

[![CI](https://github.com/cvsz/zmovie/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/cvsz/zmovie/actions/workflows/test.yml)
![Python](https://img.shields.io/badge/Python-3.11--3.14-3776AB?logo=python&logoColor=white)
![Deployment](https://img.shields.io/badge/Deployment-systemd%20%7C%20Docker-2496ED?logo=docker&logoColor=white)
![Studio](https://img.shields.io/badge/Studio-MP4%20Preview-2ea44f)
![ComfyUI](https://img.shields.io/badge/ComfyUI-API%20Integrated-2ea44f)
![Bilibili](https://img.shields.io/badge/Bilibili-Pre--Publish-orange)
![Audio](https://img.shields.io/badge/Audio-TTS%20%2B%20FFmpeg-2ea44f)
![Auto%20Publish](https://img.shields.io/badge/Auto%20Publish-OFF-critical)

`zMovie` is a self-hosted AI movie production platform that turns a concept or
reusable product brief into continuity-aware storyboards, durable AI-video
render jobs, assembled movies, and approval-gated creator-platform publishing
packages.

The original deterministic Wan-style prompt generator remains available, but
the primary application is now the full production Studio plus Product Video
Studio. Long-running production execution is isolated from uvicorn and handled
by a persistent SQLite queue and dedicated `zmovie-worker.service`.

## Documentation

Start with the [documentation index](docs/INDEX.md), which maps user, operator,
developer, contributor, and maintainer workflows to the canonical guides and
focused provider runbooks. The [status vocabulary](docs/STATUS.md) and
[documentation standard](docs/DOCUMENTATION_STANDARD.md) define how readiness,
evidence, security, and future i18n work are described.

For the resilient production runtime see:

- [Long-running render worker](docs/LONG_RUNNING_RENDER_WORKER.md)
- [Vulkan renderer isolation](docs/VULKAN_RENDERER.md)
- [Backup and recovery](docs/BACKUP_AND_RECOVERY.md)
- [Runtime evidence](docs/RUNTIME_EVIDENCE.md)

## Production status

> Status reflects verified evidence at its stated boundary. Implemented or CI-verified code is not automatically production-host, real-model, reboot, or external-publication evidence.

| Area | Status | Notes |
|---|---|---|
| Native zMovie web service | ✅ Verified previously | systemd deployment and health endpoint have production-host evidence; new resilient runtime still requires deployment acceptance on the target host |
| Public Studio | ✅ Verified previously | `https://zmovie.zeaz.dev/studio` |
| Product Video Studio | ✅ Implemented | reusable `/product` analysis/planning plus safe storyboard/project handoff into the shared production pipeline |
| Durable SQLite production queue | ✅ Implemented | atomic claims, heartbeat leases, bounded retries, pause/resume and stale recovery; exact release CI and host restart acceptance remain separate gates |
| Dedicated production worker | ✅ Implemented | `zmovie-worker.service`; long renders no longer depend on uvicorn lifetime |
| Watchdog + automatic backup timers | ✅ Implemented | rate-limited service watchdog and verified daily SQLite backup with at least 14-backup default retention |
| Studio durable status | ✅ Implemented | run/worker ID, provider, attempt, stage, heartbeat and safe error state |
| ComfyUI API integration | ✅ Verified contract | queue/history/output contract has model-free smoke evidence; remote `prompt_id` is checkpointed and reconciled after worker recovery |
| stable-diffusion.cpp CPU/Vulkan | ✅ Implemented | CPU/Vulkan controls and diagnostics exist; real model evidence depends on operator-supplied compatible weights and target-host execution |
| Accelerated AI-video production | ⚠️ Not evidenced | requires actual worker-side device/model execution and real FFprobe-valid output |
| Bilibili browser session | ✅ Verified previously | Bilibili-only state scope and live Creator Center authentication have prior evidence |
| Bilibili hardened package flow | ✅ Verified | prepare → approve → preflight gates remain explicit and fail closed |
| Real Bilibili public publication | ⏳ Pending | complete only after exact-package approval, explicit submission and confirmed genuine public URL with `remote_confirmation=true` |
| YouTube publishing | ⏸ Deferred | intentionally deferred until Bilibili completion evidence exists |

`ZeaZDev × Bilibili` is campaign creative wording for publishing through Bilibili Creator Center. It does **not** claim an official partnership, sponsorship, or endorsement by Bilibili.

## End-to-end pipeline

```text
Concept / Product brief
  ↓
Project + Character Bible / Product plan
  ↓
Scenes / Shots / Continuity Locks
  ↓
Director + QC + Provider readiness
  ↓
Durable SQLite production queue
  ↓
zmovie-worker.service
  ├─ ComfyUI local/remote
  ├─ stable-diffusion.cpp CPU/Vulkan
  └─ Generic HTTP gateway
  ↓
Persistent Render Jobs + remote prompt reconciliation
  ↓
Strict FFprobe media gate
  ↓
FFmpeg Assembly + final validation
  ↓
Bilibili Publication Package + Export
  ↓
Approval required
  ↓
Exact-package human approval
  ↓
Fail-Closed Preflight
  ↓
Explicit Creator Center submission
  ↓
Genuine public URL confirmation
```

The mock provider remains available for deterministic CI/dry-run use only and
is rejected as production AI evidence.

## Major features

- deterministic cinematic prompt engine and Wan-oriented master prompt;
- Project → Character Bible → Scene → Shot production model;
- reusable Product Video Studio with suitability scoring and claim-safe creative treatment;
- Product Studio → storyboard/project → shared production-pipeline handoff;
- continuity-in / continuity-out locks;
- storyboard, Hyperframes and production-manifest generation;
- QC scoring and strict production render gate;
- durable SQLite `worker_jobs` queue with atomic claim, heartbeat lease and bounded retry;
- dedicated `zmovie-worker.service` for unattended multi-hour rendering;
- stale-worker recovery and ComfyUI existing-`prompt_id` reconciliation;
- native ComfyUI queue/history/output integration;
- stable-diffusion.cpp CPU/Vulkan provider with worker-side device diagnostics;
- generic HTTP render gateway;
- zero-cost mock renderer for CI and dry runs only;
- persistent SQLite render jobs and asset library;
- strict real-media FFprobe validation and FFmpeg movie assembly;
- production ZIP exports;
- local account authentication and project ownership checks;
- responsive `/studio` production UI with managed MP4 previews and durable execution status;
- signed short-lived media preview URLs without exposing arbitrary filesystem paths;
- rate-limited `zmovie-watchdog.timer` service-health checks;
- verified daily `zmovie-backup.timer` SQLite online backups with integrity checks and retention;
- upgrade-readiness gate that protects active worker leases and ambiguous external publication state;
- factual runtime-evidence capture without pretending missing model weights are verified;
- hardened Bilibili prepare/approve/preflight/publish/public-confirmation workflow;
- maintained `edge-tts` Thai neural voice-over and FFmpeg mastering;
- native systemd and Docker deployments;
- automated Python 3.11–3.14, Ruff, dependency-audit, ShellCheck, frontend and Docker CI.

## One-command native install

Ubuntu/Debian, including Ubuntu under WSL with systemd enabled:

```bash
curl -fsSL https://raw.githubusercontent.com/cvsz/zmovie/main/install.sh | sudo bash
```

The installer provisions Python, FFmpeg, `espeak-ng`, Playwright Chromium, the
`zmovie` service user, persistent storage, generated admin credentials, the
hardened web service, the dedicated worker, watchdog/backup timers and health
validation. Production model weights are deliberately operator-managed and are
not automatically downloaded.

Open:

```text
http://<server-ip>:8080/studio
http://<server-ip>:8080/product
```

Production URLs:

```text
https://zmovie.zeaz.dev/studio
https://zmovie.zeaz.dev/product
```

Operations:

```bash
sudo zmovie-ctl status
sudo zmovie-ctl health
sudo zmovie-ctl worker-status
sudo zmovie-ctl watchdog-status
sudo zmovie-ctl backup-status
sudo zmovie-ctl upgrade-readiness
sudo zmovie-ctl renderer-doctor
sudo zmovie-ctl vulkan-status
sudo zmovie-ctl sdcpp-status
sudo zmovie-ctl sdcpp-evidence
```

The installer preserves `/etc/zmovie/zmovie.env`, the database, durable queue,
media, exports, publication packages, model storage and evidence across normal
upgrades. It creates a transactionally consistent SQLite online backup before
replacing application code and refuses an unsafe upgrade when in-flight work or
ambiguous external state cannot be safely reconciled.

## Docker

```bash
git clone https://github.com/cvsz/zmovie.git
cd zmovie
./install-docker.sh
```

or:

```bash
docker compose up -d --build
```

The image includes FFmpeg, `espeak-ng`, and headless Playwright Chromium. Data,
render assets and Bilibili browser state live under the persistent
`zmovie-data` volume. Native systemd is the primary deployment surface for the
separate worker/watchdog/backup services documented here.

## Local development

```bash
git clone https://github.com/cvsz/zmovie.git
cd zmovie
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
cp .env.example .env
uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

Open:

```text
http://127.0.0.1:8080/studio
http://127.0.0.1:8080/product
```

API documentation:

```text
disabled by default. To enable it locally:
ZMOVIE_ENABLE_DOCS=true uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

## ComfyUI

A hardened local ComfyUI service can be installed with:

```bash
curl -fsSL https://raw.githubusercontent.com/cvsz/zmovie/main/scripts/install-comfyui.sh | sudo bash
```

Verify the zMovie → ComfyUI queue/history/output contract without downloading a
diffusion model:

```bash
sudo bash /opt/zmovie/scripts/smoke-zmovie-comfyui.sh
```

Then inspect the production profile:

```bash
sudo zmovie-ctl doctor
sudo zmovie-ctl renderer-doctor
```

A previously verified deployment on host `core` completed the model-free smoke
path end to end using ComfyUI 0.34.0 and CPU-only PyTorch. That evidence proves
the API integration contract, not production Wan/video throughput. See
[`docs/evidence/2026-09-08-core-comfyui-smoke.md`](docs/evidence/2026-09-08-core-comfyui-smoke.md).

For a production video workflow, export ComfyUI in **API format** and configure:

```bash
sudo bash /opt/zmovie/scripts/configure-comfyui.sh \
  /path/to/workflow_api.json \
  http://127.0.0.1:8188
```

A separate/private GPU ComfyUI renderer can be used by replacing the URL with
the GPU host URL. During rendering zMovie records the remote prompt identity;
a recovered worker queries the existing remote history before any new
submission, reducing duplicate remote inference after service/host interruption.

The workflow can use placeholders such as:

```text
{{PROMPT}}
{{NEGATIVE_PROMPT}}
{{SEED}}
{{FRAMES}}
{{WIDTH}}
{{HEIGHT}}
{{FPS}}
{{PREFIX}}
```

Node-ID injection is supported through the `ZMOVIE_COMFYUI_*_NODE_IDS`
variables. Docker defaults to `http://host.docker.internal:8188` and includes
the Linux host-gateway mapping. See
[`workflows/comfyui/README.md`](workflows/comfyui/README.md).

## Full Ads Production audio

The production ad generator uses a voice-first 30-second mix with an audible
music intro and outro:

```text
0.0–1.2s
Music intro
  ↓
Thai narration + ducked soundtrack
  ↓
edge-tts 7.2.8
th-TH-PremwadeeNeural at -15%
  ↓
FFmpeg compression / sidechain ducking
  ↓
loudnorm I=-15 / TP=-1.5 / LRA=9
  ↓
AAC stereo 48 kHz
  ↓
Music/logo outro >= 1.5s
  ↓
final.mp4 locked to 30.0s
```

Production defaults:

```text
ZMOVIE_TTS_PROVIDER=edge
ZMOVIE_TTS_VOICE=th-TH-PremwadeeNeural
ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK=false
```

The one-click production generator creates an online SQLite backup first,
generates and validates the new 30-second candidate, and only then supersedes
older exact-match candidates that have no protected publish state. Candidates
with approval/submission/publication evidence, scheduled or unknown states are
preserved.

```bash
sudo bash /opt/zmovie/scripts/production-gen.sh
sudo bash /opt/zmovie/scripts/list-bilibili-publish-candidates.sh
```

The generated asset metadata records the actual TTS provider, Thai voice,
`-15%` rate, 1.2-second voice start, audio codec/sample rate/channels, exact
duration lock, campaign identity, and the fact that `ZeaZDev × Bilibili` does
not represent an official partnership.

## Bilibili Creator Center automation

The Bilibili publisher intentionally does not store a Google password or 2FA
secret. Browser state is treated as a production credential and is not placed
in durable worker queue payloads.

Verify the scoped production session:

```bash
sudo bash /opt/zmovie/scripts/verify-bilibili-session.sh
```

A real publication follows the hardened workflow:

```bash
# 1. Prepare
sudo zmovie-ctl prepare PROJECT_ID

# 2. Review exact package, then approve
sudo zmovie-ctl bili-approve PUB_JOB_ID APPROVE

# 3. External upload — only after explicit exact-package confirmation
sudo zmovie-ctl bili-publish PUB_JOB_ID CONFIRM-PUBLISH
```

A successful form submission may end in `submitted`. `submitted` is **not**
proof that the video is public. If external state becomes ambiguous, zMovie
fails closed rather than blindly retrying.

After Bilibili exposes a concrete public video URL, confirm it with the
maintained confirmation script:

```bash
sudo bash /opt/zmovie/scripts/confirm-bilibili-publication.sh \
  PUB_JOB_ID \
  'https://www.bilibili.tv/video/...'
```

Bilibili production completion requires all three durable signals:

```text
status = published
published_url = https://...bilibili.tv/.../video/...
metadata.remote_confirmation = true
```

Full guide: [`docs/BILIBILI_REAL_PUBLISH_RUNBOOK.md`](docs/BILIBILI_REAL_PUBLISH_RUNBOOK.md).

## Production API

Core v2 endpoints include:

```text
GET  /api/v2/health
GET  /api/v2/capabilities
POST /api/v2/auth/login
GET  /api/v2/projects
POST /api/v2/projects
POST /api/v2/content/storyboard
POST /api/v2/products/plan
GET  /api/v2/projects/{id}/assets
GET  /api/v2/projects/{id}/qc
GET  /api/v2/projects/{id}/production/readiness
POST /api/v2/projects/{id}/production/render
POST /api/v2/projects/{id}/production/run
GET  /api/v2/projects/{id}/production/run
GET  /api/v2/projects/{id}/production/runs/{run_id}
GET  /api/v2/worker/status
GET  /api/v2/worker/jobs/{worker_job_id}
POST /api/v2/projects/{id}/production/assemble
POST /api/v2/projects/{id}/production/export

GET  /api/v2/publish/bilibili/session
POST /api/v2/projects/{id}/publish/bilibili/prepare
POST /api/v2/publish/jobs/{id}/approve
POST /api/v2/publish/jobs/{id}/publish
GET  /api/v2/publish/jobs/{id}
```

Production `render` and `run` endpoints enqueue durable work and return rather
than keeping uvicorn responsible for multi-hour inference. Legacy prompt routes
and `zmovie.py` remain available for compatibility.

## CLI prompt generator

```bash
python zmovie.py
python zmovie.py --count 3
python zmovie.py --seed 42
python zmovie.py --seed 42 --json
```

## Persistence

SQLite stores:

- users;
- projects;
- characters;
- scenes and shots;
- render jobs and assets;
- Bilibili publish jobs;
- durable `worker_jobs` claim/lease/retry state;
- small runtime-control state such as worker pause and watchdog cooldown.

Media, exports, publication packages, browser state, model storage, backups and
runtime evidence are kept outside source control under managed runtime roots.
Native production uses `/var/lib/zmovie` for durable application state and model
storage, with verified database backups under `/var/backups/zmovie` by default.

## Security notes

- Authentication is enabled by default for the production API.
- The installer generates initial admin credentials and a signing secret.
- The web service keeps direct device access isolated; Vulkan/GPU access belongs to the worker service.
- Durable queue payloads reject credential-like fields; provider credentials remain in protected runtime configuration.
- Bilibili browser state is a credential and must not be committed, logged, or placed in queue payloads.
- Google passwords, 2FA codes and authenticator secrets are not accepted by zMovie.
- `ZMOVIE_BILIBILI_AUTO_PUBLISH=false` remains the default; real publication requires exact-package approval and explicit confirmation.
- Managed MP4 preview URLs are short-lived and scoped to media access; arbitrary filesystem paths are rejected.
- Missing model weights or renderer acceleration do not trigger watchdog restart storms.
- Production TTS fails closed by default rather than silently switching to a robotic local voice.
- Use TLS/reverse proxy/Cloudflare Tunnel when exposing the service to the internet.

## Tests

```bash
python3 -m pip install -r requirements.txt
python3 -m compileall -q zmovie.py app.py main.py zmovie_platform tests
python3 -m unittest discover -s tests -v
python3 scripts/verify_docs.py
node --check static/durable-worker.js
node --check static/product.js
shellcheck --severity=warning install.sh install-docker.sh scripts/*.sh
docker compose config --quiet
docker build -t zmovie:test .
```

CI validates Python 3.11–3.14, durable queue/recovery behavior, ComfyUI
prompt-id reconciliation, Product Studio and Studio JavaScript, installer and
operations scripts, SQLite backup logic, deterministic prompt output, provider
contracts, Bilibili publication safety transitions, dependency/security quality
gates and the production container build without making external inference or
publication calls.

Passing CI is not production-host, reboot, Vulkan or real-model evidence. Use
[Testing](docs/TESTING.md) and [Runtime evidence](docs/RUNTIME_EVIDENCE.md) for
those acceptance boundaries.

## License

zMovie is licensed under the MIT License. See [`LICENSE`](LICENSE).
