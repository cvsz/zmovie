# zMovie

`zMovie` is a self-hosted AI movie production platform that turns a concept into continuity-aware storyboards, AI-video render jobs, assembled movies, and creator-platform publishing packages.

The original deterministic Wan-style prompt generator remains available, but the primary application is now the full production Studio.

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
Final Movie
  ↓
Bilibili Publication Package
  ↓
Review / Approval
  ↓
Playwright Creator Center Upload
  ↓
Publish Now / Scheduled Release
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
- Bilibili Creator Center publishing with one-time manual Google login and reusable browser session;
- responsive `/studio` production UI;
- native systemd and Docker deployments;
- automated Python and Docker CI.

## One-command native install

Ubuntu/Debian, including Ubuntu under WSL with systemd enabled:

```bash
curl -fsSL https://raw.githubusercontent.com/cvsz/zmovie/main/install.sh | sudo bash
```

The installer provisions Python, FFmpeg, Playwright Chromium, the `zmovie` service user, persistent storage, generated admin credentials, a hardened systemd unit, and a health check.

Open:

```text
http://<server-ip>:8080/studio
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

The image includes FFmpeg and headless Playwright Chromium. Data, render assets and Bilibili browser state live under the persistent `zmovie-data` volume.

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
http://127.0.0.1:8080/docs
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

## Bilibili Creator Center automation

The Bilibili publisher intentionally does not store a Google password or 2FA secret.

Run the one-time interactive Google sign-in on a GUI machine:

```bash
python -m zmovie_platform.publishers.bilibili login
```

Complete Google authentication in the browser and press Enter in the terminal. zMovie stores only Playwright browser session state.

Then a completed project can follow:

```bash
python -m zmovie_platform.publishers.bilibili prepare --project PROJECT_ID
python -m zmovie_platform.publishers.bilibili approve --job PUB_JOB_ID
python -m zmovie_platform.publishers.bilibili publish --job PUB_JOB_ID
```

The Studio exposes the same workflow with an explicit approval boundary. Current Creator Center constraints encoded by zMovie include 100-character titles, 2000-character introductions, at most 10 tags, a 1280×720 generated cover, and scheduled-release validation between +2 hours and +15 days.

Full guide: [`docs/BILIBILI_PUBLISHING.md`](docs/BILIBILI_PUBLISHING.md).

## Production API

Core v2 endpoints:

```text
GET  /api/v2/health
GET  /api/v2/capabilities
POST /api/v2/auth/login
GET  /api/v2/projects
POST /api/v2/projects
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
- Use TLS/reverse proxy/Cloudflare Tunnel when exposing the service to the internet.

## Tests

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

CI validates supported Python versions, installer/operations shell syntax, the model-free ComfyUI workflow, deterministic prompt output, the project pipeline, provider contracts, Bilibili publication-package state transitions, and the production container build without making external inference or publication calls.

## License

Use and adapt for your own zMovie workflows.
