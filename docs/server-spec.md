# zMovie Server Specification

## 1. Purpose

This document defines the production server specification for `zmovie.zeaz.dev`.
It covers runtime topology, service configuration, storage layout, security boundaries,
networking, observability, backup, upgrade, and local model fullstack integration.

## 2. Runtime Topology

- **Host OS:** Ubuntu 22.04/24.04 or Debian 12/13
- **Process model:** systemd-managed single service
- **Service user:** `zmovie` (system account, no login shell)
- **Service file:** `/etc/systemd/system/zmovie.service`
- **Executable:** `/opt/zmovie/.venv/bin/uvicorn main:app`
- **Entrypoint:** `main:app`
- **Port:** `8080` by default, configurable via `ZMOVIE_PORT`
- **Workers:** `1`
- **Reverse proxy:** optional; if present, terminate TLS upstream and set `--proxy-headers`

## 3. Filesystem Layout

| Path | Purpose |
|---|---|
| `/opt/zmovie/` | Application code and venv |
| `/opt/zmovie/.venv/` | Python virtualenv |
| `/var/lib/zmovie/` | Persistent data root |
| `/var/lib/zmovie/media/` | Media exports and previews |
| `/var/lib/zmovie/exports/` | Final movie exports |
| `/var/lib/zmovie/objects/` | Object storage |
| `/var/lib/zmovie/publish/` | Publish artifacts |
| `/var/lib/zmovie/bilibili/` | Browser session state |
| `/var/lib/zmovie/playwright/` | Playwright browser binaries |
| `/var/lib/zmovie/audit.jsonl` | Audit log |
| `/etc/zmovie/` | Configuration directory |
| `/etc/zmovie/zmovie.env` | Runtime environment file |
| `/var/backups/zmovie/` | Database backups |
| `/var/lib/zmovie/models/` | Local model artifacts |
| `/var/lib/zmovie/models/piper/` | Piper voice models |
| `/var/lib/zmovie/models/whisper/` | Whisper model cache |
| `/opt/zmovie-local-models/.venv/` | Local model Python venv |
| `/var/lib/ollama/models/` | Ollama model storage |

## 4. Environment Configuration

Required variables in `/etc/zmovie/zmovie.env`:

```bash
ZMOVIE_HOST=0.0.0.0
ZMOVIE_PORT=8080
ZMOVIE_DB_PATH=/var/lib/zmovie/zmovie.db
ZMOVIE_MEDIA_ROOT=/var/lib/zmovie/media
ZMOVIE_EXPORT_ROOT=/var/lib/zmovie/exports
ZMOVIE_PUBLISH_ROOT=/var/lib/zmovie/publish
ZMOVIE_OBJECT_ROOT=/var/lib/zmovie/objects
ZMOVIE_AUDIT_PATH=/var/lib/zmovie/audit.jsonl
ZMOVIE_AUTH_ENABLED=true
ZMOVIE_ENABLE_DOCS=false
ZMOVIE_SECRET_KEY=<random 64-hex>
ZMOVIE_ADMIN_USER=admin
ZMOVIE_ADMIN_PASSWORD=<random>
ZMOVIE_TOKEN_TTL=86400
ZMOVIE_CORS_ORIGINS=
ZMOVIE_COMFYUI_URL=http://127.0.0.1:8188
ZMOVIE_COMFYUI_WORKFLOW=/opt/zmovie/workflows/comfyui/smoke_api.json
ZMOVIE_COMFYUI_TIMEOUT=3600
ZMOVIE_TTS_PROVIDER=edge
ZMOVIE_TTS_VOICE=th-TH-PremwadeeNeural
ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK=false
ZMOVIE_PROVIDER_WEBHOOK=
ZMOVIE_PROVIDER_TOKEN=
ZMOVIE_BILIBILI_STUDIO_URL=https://studio.bilibili.tv/
ZMOVIE_BILIBILI_STATE_PATH=/var/lib/zmovie/bilibili/storage_state.json
ZMOVIE_BILIBILI_HEADLESS=true
ZMOVIE_BILIBILI_AUTO_PUBLISH=false
ZMOVIE_BILIBILI_TIMEOUT_MS=120000
PLAYWRIGHT_BROWSERS_PATH=/var/lib/zmovie/playwright
```

Local model optional variables:

```bash
ZMOVIE_LOCAL_MODELS_ENABLED=false
ZMOVIE_LOCAL_LLM_ENDPOINT=http://127.0.0.1:11434
ZMOVIE_LOCAL_LLM_MODEL=
ZMOVIE_LOCAL_PIPER_VOICE=
ZMOVIE_LOCAL_WHISPER_MODEL=
```

## 5. Security Boundaries

- Authentication is enabled by default.
- Legacy admin routes require `role == "admin"`.
- Media preview tokens are short-lived and audience-scoped.
- Asset paths are validated against managed roots and symlink escapes are rejected.
- Security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, CSP.
- Secrets are never logged.
- The installer does not print generated credentials to stdout.
- Private keys and credentials are excluded from version control.

## 6. Database

- Engine: SQLite
- Path: `/var/lib/zmovie/zmovie.db`
- Pragmas: `journal_mode=WAL`, `foreign_keys=ON`
- Schema managed via idempotent `CREATE TABLE IF NOT EXISTS` blocks
- Backups stored in `/var/backups/zmovie/` with integrity and foreign-key checks

## 7. Providers

| Provider | Modes | Notes |
|---|---|---|
| `mock` | text-to-video | Local dry-run; always configured |
| `webhook` | text-to-video, image-to-video | Requires `ZMOVIE_PROVIDER_WEBHOOK` |
| `comfyui` | text-to-video, image-to-video | Requires workflow JSON and reachable ComfyUI |
| `sdcpp` | text-to-video | Local stable-diffusion.cpp; requires sd-cli and video model |
| `ollama` | text-to-text | Optional local LLM; enabled by feature flag |

## 8. Local Model Fullstack

Install only on nodes with sufficient RAM/VRAM.

- **LLM:** Ollama at `http://127.0.0.1:11434`
- **TTS:** Piper with local ONNX voice models
- **STT:** faster-whisper in dedicated venv `/opt/zmovie-local-models/.venv`
- **Feature flag:** `ZMOVIE_LOCAL_MODELS_ENABLED=true`
- **Artifacts:** `/var/lib/zmovie/models/`
- **Setup script:** `scripts/setup-ha-node-a-local-models.sh`

## 9. WireGuard VPN Integration

zMovie supports multi-node remote access via WireGuard.

- Router endpoint: `b8ff0b738b04.sn.mynetname.net:51820`
- Server public key: `kt9MF9J+JNbq8bxYpYV3QWzpX6s0AOcVV6J1KUfdowo=`
- Client VPN subnet: `10.8.0.0/24`
- Management LAN: `192.168.1.0/24`

Client setup scripts:

- `scripts/setup-policedbc-wireguard.sh`
- `scripts/setup-ha-node-a-wireguard.sh`
- `scripts/setup-ha-node-b-wireguard.sh`

Verification scripts:

- `scripts/verify-policedbc-wireguard.sh`
- `scripts/verify-ha-node-a-wireguard.sh`
- `scripts/verify-ha-node-b-wireguard.sh`

Repair scripts:

- `scripts/repair-policedbc-wireguard.sh`
- `scripts/repair-ha-node-a-wireguard.sh`
- `scripts/repair-ha-node-b-wireguard.sh`

MikroTik peer registration snippets:

- `scripts/policedbc-mikrotik-peer-add.rsc`
- `scripts/ha-node-a-mikrotik-peer-add.rsc`
- `scripts/ha-node-b-mikrotik-peer-add.rsc`

## 10. Networking

- Bind: `0.0.0.0:8080` or as configured
- Reverse proxy: recommended for TLS termination
- Firewall: allow `8080/tcp` and `51820/udp` as needed
- CORS: controlled by `ZMOVIE_CORS_ORIGINS`

## 11. Observability

- Health: `/api/v2/health`
- Capabilities: `/api/v2/capabilities`
- Audit log: `/var/lib/zmovie/audit.jsonl`
- Systemd journal: `journalctl -u zmovie`
- Operator CLI: `/usr/local/bin/zmovie-ctl`

## 12. Backup and Recovery

- Backup script: `install.sh --backup` or manual SQLite backup
- Backup directory: `/var/backups/zmovie/`
- Verification: integrity check + foreign-key check before swap
- Restore: replace database file and restart service

## 13. Upgrade Procedure

1. Run backup:
```bash
sudo /opt/zmovie/install.sh --backup
```

2. Pull code or run installer:
```bash
sudo /opt/zmovie/install.sh --upgrade
```

3. Verify:
```bash
sudo systemctl status zmovie
curl -fsS http://127.0.0.1:8080/api/v2/health
```

4. Rollback if needed:
```bash
sudo /opt/zmovie/install.sh --uninstall
# restore from /var/backups/zmovie/
```

## 14. Hardware Target: Dell PowerEdge T30 / VMware / Ubuntu 26.04

### 14.1 Validated Host Hardware

Source: CPU-Z validator `https://valid.cpuid.com/se9qe6vt`

| Component | Validated Spec | Notes |
|---|---|---|
| **CPU** | Intel Xeon E3-1225 v5 @ 3.30GHz | 4 cores / 4 threads, 8MB L3, 80W TDP, VT-x, AES, AVX2 |
| **Motherboard** | Dell 07T4MC (LGA1151, Intel C236) | BIOS 1.15.0 |
| **RAM** | 32GB DDR4-3200 (2x16GB SK Hynix) | Currently running at DDR4-2128; enable XMP/DOCP for full speed |
| **GPU** | NVIDIA GeForce 210 1024MB DDR3 | **Not suitable for GPU acceleration**; driver from 2015 |
| **Integrated GPU** | Intel HD Graphics P530 | Used for display output |
| **Storage** | Samsung SSD 870 QVO 1TB (OS) | 77% used, 98% health |
| **Storage** | WDC WD10EZEX 1TB | 10% used |
| **Storage** | WDC WD20EZRZ 2TB | 57% used, 377k load cycles (exceeds 300k rating) |
| **OS (host)** | Windows 11 Enterprise 24H2 | For ESXi deployment, install/replace with ESXi |

### 14.2 Resource Allocation Guidance

| Workload | vCPU | RAM | Notes |
|---|---|---|---|
| zMovie API + workers | 2–4 vCPU | 8–12GB | Primary VM workload |
| ComfyUI renderer | 2–4 vCPU | 8–16GB | **CPU-only on this host**; GeForce 210 cannot accelerate |
| Local model fullstack | 2–4 vCPU | 8–16GB | CPU inference; no GPU acceleration available |
| Combined in one VM | 4 vCPU | 16–24GB | Conservative fit on 4C/4T Xeon with 32GB RAM |

### 14.3 VGA/GPU Reality Check

- **NVIDIA GeForce 210:** 1GB DDR3, 16 cores, driver 341.74 from 2015. This card cannot run modern CUDA compute, TensorRT, or Vulkan ML workloads. Treat it as display-only.
- **Intel HD Graphics P530:** Integrated; no discrete VRAM for ML acceleration.
- **VMware GPU passthrough:** The GeForce 210 can be passed through for display, but it will not accelerate ComfyUI or local model inference.
- **Expected acceleration mode:** CPU-only for ComfyUI (`accelerated=false`) and local Ollama/Whisper inference. Plan render times accordingly.

### 14.4 BIOS/UEFI Recommendations

- Enable XMP/DOCP to restore RAM from DDR4-2128 to DDR4-3200
- Enable VT-x/VT-d in BIOS for VMware hardware virtualization
- Consider moving display cable to GeForce 210 if GPU passthrough is desired

### 14.5 Storage Recommendations

- Use the Samsung SSD 870 QVO 1TB for VM datastore and zMovie database
- Monitor the WDC WD20EZRZ load cycles; consider replacing if cycles increase rapidly
- Keep regular backups on the 2TB HDD

### 14.6 Deployment Model

- Install VMware ESXi on the T30
- Create a single Ubuntu 26.04 VM with 4–6 vCPU and 24–32GB RAM
- Mount SSD datastore for VM and zMovie data
- Run zMovie as a systemd service inside the VM
- Expect CPU-bound performance for renders and local inference

## 15. CI/CD

- Workflow: `.github/workflows/test.yml`
- Jobs: `python`, `docker`, `quality`
- Python matrix: `3.11`, `3.12`, `3.13`, `3.14`
- Quality gates: `ruff`, `pip-audit`, `shellcheck`, JS syntax, script syntax, compose validation

## 16. Known Gaps and External Dependencies

- ComfyUI acceleration depends on host GPU/driver setup
- sdcpp video mode requires explicit model and backend configuration
- Bilibili publishing requires one-time interactive browser login
- Local model stack requires manual host setup via `scripts/setup-ha-node-a-local-models.sh`
