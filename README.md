# zMovie

`zMovie` is a reusable cinematic prompt generator for AI-video workflows, initially focused on Wan 3.0-style 20-second continuous action long takes.

It now ships as both a deterministic CLI generator and a self-hosted full-stack web application.

## Features

- Production-ready Wan 3.0 master action prompt specification.
- Randomized setting, character styling, attacker archetype, choreography, camera, lighting, destruction, and ending.
- Deterministic generation with a numeric seed.
- Plain-text and JSON CLI output.
- FastAPI REST API.
- Responsive browser UI with copy-ready main and negative prompts.
- Local SQLite generation history; no external database required.
- One-command Ubuntu/Debian installer with a hardened systemd service.
- Dockerfile and Docker Compose deployment.
- Automated Python and container CI.

## One-command automated install

On Ubuntu/Debian, including Ubuntu systems running under WSL with systemd enabled:

```bash
curl -fsSL https://raw.githubusercontent.com/cvsz/zmovie/main/install.sh | sudo bash
```

The installer is designed to be safe to run again. It:

1. installs Python, venv, Git, curl, and CA certificates;
2. creates the dedicated `zmovie` service account;
3. clones or fast-forwards `cvsz/zmovie` into `/opt/zmovie`;
4. creates `/opt/zmovie/.venv` and installs runtime dependencies;
5. creates `/etc/zmovie/zmovie.env` on first install and preserves it on later runs;
6. installs and enables `zmovie.service` when systemd is available;
7. starts/restarts the application and verifies `/api/health` before reporting success.

Default web URL:

```text
http://<server-ip>:8080/
```

Service operations:

```bash
sudo systemctl status zmovie
sudo journalctl -u zmovie -f
sudo systemctl restart zmovie
```

### Installer overrides

Environment variables can override deployment settings:

```bash
sudo ZMOVIE_PORT=8090 \
  ZMOVIE_INSTALL_DIR=/opt/zmovie \
  ZMOVIE_SERVICE_USER=zmovie \
  bash install.sh
```

Supported installer variables:

| Variable | Default |
|---|---|
| `ZMOVIE_REPO_URL` | `https://github.com/cvsz/zmovie.git` |
| `ZMOVIE_BRANCH` | `main` |
| `ZMOVIE_INSTALL_DIR` | `/opt/zmovie` |
| `ZMOVIE_SERVICE_USER` | `zmovie` |
| `ZMOVIE_ENV_DIR` | `/etc/zmovie` |
| `ZMOVIE_PORT` | `8080` on first install |

> Existing `/etc/zmovie/zmovie.env` is intentionally preserved during upgrades. Edit it directly when changing an already-installed service configuration, then restart `zmovie`.

## Docker Compose

```bash
git clone https://github.com/cvsz/zmovie.git
cd zmovie
docker compose up -d --build
```

Then open:

```text
http://localhost:8080/
```

Use a different host port:

```bash
ZMOVIE_PORT=8090 docker compose up -d --build
```

Generation history persists in the `zmovie-data` Docker volume.

## Local development

```bash
git clone https://github.com/cvsz/zmovie.git
cd zmovie
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python app.py
```

The web app defaults to `http://127.0.0.1:8080/` when opened locally through the bound host interface.

## REST API

FastAPI exposes interactive API documentation at:

```text
/docs
```

Core endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | GET | service health/version |
| `/api/options` | GET | generator variable catalog |
| `/api/generate` | POST | generate one or more prompts |
| `/api/history` | GET | recent saved generations |
| `/api/history/{id}` | GET | one saved generation |

Example:

```bash
curl -s http://127.0.0.1:8080/api/generate \
  -H 'content-type: application/json' \
  -d '{"seed":42,"count":1,"save_history":true}'
```

## CLI

The original dependency-free core remains directly usable:

```bash
python zmovie.py
python zmovie.py --count 3
python zmovie.py --seed 42
python zmovie.py --seed 42 --json
python zmovie.py --count 10 > prompts.txt
```

## Prompt timing model

Each generated video prompt follows a 20-second uninterrupted long-take structure:

| Time | Beat |
|---|---|
| 0:00–0:03 | Character introduction + threat appears |
| 0:03–0:06 | First exchange |
| 0:06–0:09 | Reversal / escalation |
| 0:09–0:12 | Environmental impact |
| 0:12–0:16 | Peak continuous combat |
| 0:16–0:18 | Decisive finishing move |
| 0:18–0:20 | Composed cinematic ending |

## Architecture

```text
Browser
  |
  v
FastAPI (app.py)
  |-- /static/*             responsive web frontend
  |-- /api/generate         generation API
  |-- /api/history          SQLite history API
  |
  +--> zmovie.py            deterministic prompt engine
  |
  +--> data/zmovie.db       local persistent history
```

The master prompt specification lives at [`prompts/WAN3_MASTER_ACTION_GENERATOR.md`](prompts/WAN3_MASTER_ACTION_GENERATOR.md).

## Production notes

The built-in application has no user authentication. If it is exposed to the public internet, put it behind an authenticated reverse proxy, access gateway, VPN, or another trusted perimeter. The native installer uses a dedicated non-login service account and systemd hardening, but perimeter authentication remains a deployment responsibility.

For Cloudflare Tunnel, route the chosen hostname to the local HTTP service, for example `http://localhost:8080`, while keeping direct inbound access to port 8080 blocked if the service is intended to be tunnel-only.

## Tests

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

GitHub Actions tests Python 3.11, 3.12, and 3.13, CLI output, API behavior, and Docker image construction.

## License

Use and adapt for your own zMovie workflows.
