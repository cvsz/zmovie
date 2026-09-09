# zMovie

[![CI](https://github.com/cvsz/zmovie/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/cvsz/zmovie/actions/workflows/test.yml)
![Python](https://img.shields.io/badge/Python-3.11--3.14-3776AB?logo=python&logoColor=white)
![Deployment](https://img.shields.io/badge/Deployment-systemd%20%7C%20Docker-2496ED?logo=docker&logoColor=white)
![Studio](https://img.shields.io/badge/Studio-MP4%20Preview-2ea44f)
![ComfyUI](https://img.shields.io/badge/ComfyUI-API%20Integrated-2ea44f)
![Bilibili](https://img.shields.io/badge/Bilibili-Pre--Publish-orange)
![Audio](https://img.shields.io/badge/Audio-TTS%20%2B%20FFmpeg-2ea44f)
![Auto%20Publish](https://img.shields.io/badge/Auto%20Publish-OFF-critical)

`zMovie` is a self-hosted AI movie production platform that turns a concept into continuity-aware storyboards, AI-video render jobs, assembled movies, and creator-platform publishing packages.

The original deterministic Wan-style prompt generator remains available, but the primary application is now the full production Studio.

## Production status

> Status reflects verified implementation/runtime evidence. A feature is not marked complete when only code exists or when external publication has not been remotely confirmed.

| Area | Status | Notes |
|---|---|---|
| Native zMovie service | ✅ Verified | systemd deployment and health endpoint verified on the production host |
| Public Studio | ✅ Verified | `http://zmovie.zeaz.dev/studio` |
| Studio MP4 preview | ✅ Implemented | signed managed-media preview URLs with browser video controls |
| Managed project reset | ✅ Implemented | transactional SQLite backup, `prj_*` cleanup, rollback-safe regeneration |
| ComfyUI API integration | ✅ Verified | queue/history/output contract verified with model-free smoke workflow |
| Accelerated AI-video production | ⚠️ Not evidenced | current verified host is CPU-only; real accelerated video model throughput is not proven |
| Bilibili browser session | ✅ Verified | Bilibili-only state scope and live Creator Center authentication verified |
| Bilibili hardened package flow | ✅ Verified | prepare → approve → preflight gates exercised with a real managed MP4 |
| Full Ads Production | ✅ Implemented | `ZeaZDev × Bilibili` 30-second creator-publishing campaign generator |
| Voice-over / soundtrack | ✅ Implemented | Edge/Bing TTS primary, local `espeak-ng` fallback, FFmpeg mix/ducking/loudness normalization |
| Real Bilibili public publication | ⏳ Pending | complete only after live upload plus confirmed public URL and `remote_confirmation=true` |
| YouTube publishing | ⏸ Deferred | intentionally deferred until Bilibili completion evidence exists |

`ZeaZDev × Bilibili` is campaign creative wording for publishing through Bilibili Creator Center. It does **not** claim an official partnership, sponsorship, or endorsement by Bilibili.

## End-to-end pipeline

```text
Concept
  ↓
Project + Character Bible
  ↓
Scenes / Shots / Continuity Locks
  ↓
Director + QC
  ↓
Render Provider
  ├─ ComfyUI
  ├─ Generic HTTP gateway
  └─ Local mock / dry run
  ↓
Persistent Render Jobs + Asset Library
  ↓
FFmpeg Assembly
  ↓
Final Movie + Audio Mix
  ↓
Studio MP4 Preview
  ↓
Bilibili Publication Package
  ↓
Review / Approval
  ↓
Fail-Closed Preflight
  ↓
Playwright Creator Center Upload
  ↓
Public URL Confirmation
```

## Major features

- deterministic cinematic prompt engine and Wan-oriented master prompt;
- Project → Character Bible → Scene → Shot production model;
- continuity-in / continuity-out locks;
- storyboard and production-manifest generation;
- QC scoring and render gate;
- provider abstraction;
- native ComfyUI queue/history/output integration;
- generic HTTP render gateway;
- zero-cost mock renderer for CI and dry runs;
- persistent SQLite render jobs and asset library;
- FFmpeg movie assembly;
- production ZIP exports;
- local account authentication and project ownership checks;
- audit trail, metrics, health, backup and security headers;
- responsive `/studio` production UI with managed MP4 previews;
- signed short-lived media preview URLs without exposing arbitrary filesystem paths;
- Bilibili Creator Center publishing with one-time manual Google login and reusable browser session;
- hardened Bilibili prepare/approve/preflight/publish/public-confirmation workflow;
- rollback-safe `prj_*` project cleanup and production regeneration;
- `ZeaZDev × Bilibili` Full Ads Production generator;
- Edge/Bing TTS voice-over with local `espeak-ng` fallback;
- FFmpeg-generated soundtrack, voice/music ducking, AAC stereo output, and `loudnorm` mastering;
- native systemd and Docker deployments;
- automated Python and Docker CI.

## One-command native install

Ubuntu/Debian, including Ubuntu under WSL with systemd enabled:

```bash
curl -fsSL https://raw.githubusercontent.com/cvsz/zmovie/main/install.sh | sudo bash
```

The installer provisions Python, FFmpeg, `espeak-ng`, Playwright Chromium, the `zmovie` service user, persistent storage, generated admin credentials, a hardened systemd unit, and a health check.

Open:

```text
http://<server-ip>:8080/studio
```

Production Studio:

```text
http://zmovie.zeaz.dev/studio
```

Operations:

```bash
sudo systemctl status zmovie
sudo journalctl -u zmovie -f
sudo bash /opt/zmovie/install.sh upgrade
sudo bash /opt/zmovie/install.sh backup
sudo bash /opt/zmovie/scripts/doctor.sh
```

The installer preserves `/etc/zmovie/zmovie.env` and the database across upgrades and creates a transactionally consistent SQLite online backup before replacing application code.

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

The image includes FFmpeg, `espeak-ng`, and headless Playwright Chromium. Data, render assets and Bilibili browser state live under the persistent `zmovie-data` volume.

## Local development

```bash
git clone https://github.com/cvsz/zmovie.git
cd zmovie
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

Open:

```text
http://127.0.0.1:8080/studio
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

Verify the zMovie → ComfyUI queue/history/output contract without downloading a diffusion model:

```bash
sudo bash /opt/zmovie/scripts/smoke-zmovie-comfyui.sh
```

Then inspect the production profile:

```bash
sudo bash /opt/zmovie/scripts/doctor.sh
```

A verified deployment on host `core` completed this smoke path end to end using ComfyUI 0.34.0 and a CPU-only PyTorch runtime. That evidence proves the integration contract, not production Wan/video throughput. See [`docs/evidence/2026-09-08-core-comfyui-smoke.md`](docs/evidence/2026-09-08-core-comfyui-smoke.md).

For a production video workflow, export ComfyUI in **API format** and configure:

```bash
sudo bash /opt/zmovie/scripts/configure-comfyui.sh \
  /path/to/workflow_api.json \
  http://127.0.0.1:8188
```

The same zMovie host can use a separate/private GPU ComfyUI renderer by replacing the URL with the GPU host URL; the workflow JSON remains on the zMovie host and is submitted to that ComfyUI API.

The workflow can use placeholders such as:

```text
{{PROMPT}}
{{NEGATIVE_PROMPT}}
{{SEED}}
{{FRAMES}}
{{WIDTH}}
{{HEIGHT}}
{{FPS}}
{{FILENAME_PREFIX}}
```

Node-ID injection is also supported through the `ZMOVIE_COMFYUI_*_NODE_IDS` variables. Docker defaults to `http://host.docker.internal:8188` and includes the Linux host-gateway mapping.

See [`workflows/comfyui/README.md`](workflows/comfyui/README.md).

## Full Ads Production audio

The production ad generator no longer uses a silent `anullsrc` track. The current audio chain is:

```text
Narration
  ↓
Edge/Bing TTS (default: en-US-AriaNeural)
  ↓ fallback
espeak-ng local TTS

Generated soundtrack
  ↓
FFmpeg voice/music mix + ducking
  ↓
loudnorm I=-16 / TP=-1.5 / LRA=11
  ↓
AAC stereo 48 kHz
  ↓
final.mp4
```

Native defaults:

```text
ZMOVIE_TTS_PROVIDER=edge
ZMOVIE_TTS_VOICE=en-US-AriaNeural
```

Generate a clean production candidate with backup/rollback protection:

```bash
sudo bash /opt/zmovie/scripts/reset-production-projects.sh DELETE-ALL-PRJ
sudo bash /opt/zmovie/scripts/list-bilibili-publish-candidates.sh
```

The generated asset metadata records the actual TTS provider, audio codec/sample rate/channels, campaign identity, and the fact that `ZeaZDev × Bilibili` does not represent an official partnership.

## Bilibili Creator Center automation

The Bilibili publisher intentionally does not store a Google password or 2FA secret. Browser state is treated as a production credential.

Verify the scoped production session:

```bash
sudo bash /opt/zmovie/scripts/verify-bilibili-session.sh
```

A real publication follows the hardened workflow:

```bash
# 1. Prepare
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a; source /etc/zmovie/zmovie.env; set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened prepare --project PROJECT_ID
'

# 2. Review exact package, then approve
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a; source /etc/zmovie/zmovie.env; set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened approve --job PUB_JOB_ID
'

# 3. Fail-closed preflight
sudo bash /opt/zmovie/scripts/preflight-bilibili-publish.sh PUB_JOB_ID

# 4. External upload — only after explicit operator approval
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a; source /etc/zmovie/zmovie.env; set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened publish --job PUB_JOB_ID
'
```

A successful form submission may end in `submitted`. `submitted` is **not** proof that the video is public.

After Bilibili exposes a concrete public video URL, confirm it:

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

Core v2 endpoints:

```text
GET  /api/v2/health
GET  /api/v2/capabilities
POST /api/v2/auth/login
GET  /api/v2/projects
POST /api/v2/projects
GET  /api/v2/projects/{id}/assets
GET  /api/v2/projects/{id}/qc
POST /api/v2/projects/{id}/render
POST /api/v2/projects/{id}/assemble
POST /api/v2/projects/{id}/export
POST /api/v2/pipeline

GET  /api/v2/publish/bilibili/session
POST /api/v2/projects/{id}/publish/bilibili/prepare
POST /api/v2/publish/jobs/{id}/approve
POST /api/v2/publish/jobs/{id}/publish
GET  /api/v2/publish/jobs/{id}
```

Legacy prompt-generation endpoints and `zmovie.py` remain available for compatibility.

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
- render jobs;
- assets;
- Bilibili publish jobs.

Media, exports, publication packages, browser state and other runtime data are kept under `data/` locally or `/var/lib/zmovie` with the native installer.

## Security notes

- Authentication is enabled by default for the production API.
- The installer generates initial admin credentials and a signing secret.
- Bilibili browser state is a credential and must not be committed or shared.
- Google passwords, 2FA codes and authenticator secrets are not accepted by zMovie.
- `ZMOVIE_BILIBILI_AUTO_PUBLISH=false` is the default; real publication requires an approved publish job.
- Managed MP4 preview URLs are short-lived and scoped to media access; arbitrary filesystem paths are rejected.
- Use TLS/reverse proxy/Cloudflare Tunnel when exposing the service to the internet.

## Tests

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

CI validates supported Python versions, Studio preview JavaScript syntax, installer/operations shell syntax, the model-free ComfyUI workflow, deterministic prompt output, the project pipeline, provider contracts, Bilibili publication-package state transitions, ad-candidate metadata, and the production container build without making external inference or publication calls.

## License

Use and adapt for your own zMovie workflows.
