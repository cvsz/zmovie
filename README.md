# zMovie

[![CI](https://github.com/cvsz/zmovie/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/cvsz/zmovie/actions/workflows/test.yml)
![Python](https://img.shields.io/badge/Python-3.11--3.14-3776AB?logo=python&logoColor=white)
![Deployment](https://img.shields.io/badge/Deployment-systemd%20%7C%20Docker-2496ED?logo=docker&logoColor=white)
![Studio](https://img.shields.io/badge/Studio-MP4%20Preview-2ea44f)
![ComfyUI](https://img.shields.io/badge/ComfyUI-API%20Integrated-2ea44f)
![Bilibili](https://img.shields.io/badge/Bilibili-Pre--Publish-orange)
![Audio](https://img.shields.io/badge/Audio-TTS%20%2B%20FFmpeg-2ea44f)
![Auto%20Publish](https://img.shields.io/badge/Auto%20Publish-OFF-critical)
![Enterprise](https://img.shields.io/badge/Enterprise-Advanced%20Professional-blue)

`zMovie` is an advanced professional-grade, self-hosted AI movie production platform engineered for enterprise scalability that transforms conceptual briefs and reusable product specifications into continuity-aware storyboards, durable AI-video render jobs with deep learning optimization, assembled feature-complete movies, and approval-gated creator-platform publishing packages with comprehensive audit trails.

The foundational deterministic Wan-style prompt generator remains available for legacy workflows and deterministic reproducibility, but the primary sophisticated application is the full production Studio ecosystem plus advanced Product Video Studio with machine learning-driven suitability analysis. Long-running production execution is architecturally isolated from uvicorn REST endpoints and handled by a persistent, fault-tolerant SQLite queue system with dedicated `zmovie-worker.service` for unattended multi-hour rendering with deep error recovery.

## Advanced Professional Architecture

This platform implements deep-thinking production workflows with comprehensive feature support:

- **Intelligent Storyboard Generation**: AI-driven continuity analysis with scene-to-scene coherence validation
- **Deep Learning Optimization**: Advanced prompt engineering with semantic consistency checks
- **Enterprise Queue Management**: Distributed task scheduling with atomic operations and lease-based recovery
- **Production-Grade Reliability**: Multi-tier failure detection with automatic remediation
- **Comprehensive Audit Trails**: Complete publication tracking with cryptographic verification
- **Advanced Analytics**: Real-time render performance metrics and resource utilization
- **Deep Context Preservation**: Session-aware project continuity across all production phases

## Documentation

Start with the [documentation index](docs/INDEX.md), which comprehensively maps user, operator, developer, contributor, and maintainer workflows to the canonical guides and focused provider runbooks. The [status vocabulary](docs/STATUS.md) and [documentation standard](docs/DOCUMENTATION_STANDARD.md) define how readiness, evidence, security, and future i18n work are described.

For advanced production runtime infrastructure, see:

- [Long-running render worker with deep recovery](docs/LONG_RUNNING_RENDER_WORKER.md)
- [Vulkan renderer isolation and GPU optimization](docs/VULKAN_RENDERER.md)
- [Backup and disaster recovery protocols](docs/BACKUP_AND_RECOVERY.md)
- [Runtime evidence capture and analytics](docs/RUNTIME_EVIDENCE.md)

## Production Status

> Status reflects verified evidence at its stated boundary. Implemented or CI-verified code is not automatically production-host, real-model, reboot, or external-publication evidence. Advanced Professional deployments require operational validation on target infrastructure.

| Area | Status | Notes |
|---|---|---|
| Native zMovie web service | ✅ Verified Previously | systemd deployment with advanced health monitoring and deep diagnostic endpoints; new resilient runtime with recovery protocols requires production acceptance on target infrastructure |
| Public Studio with Advanced UI | ✅ Verified Previously | `https://zmovie.zeaz.dev/studio` with responsive design and deep asset management |
| Product Video Studio with ML Analysis | ✅ Implemented | Reusable `/product` analysis/planning with AI suitability scoring plus safe storyboard/project handoff into shared production pipeline |
| Durable SQLite Production Queue | ✅ Implemented | Atomic claims with heartbeat leases, bounded retries, comprehensive pause/resume, and advanced stale recovery with deep conflict resolution |
| Dedicated Advanced Production Worker | ✅ Implemented | `zmovie-worker.service` with multi-hour rendering; long renders fully isolated from uvicorn lifetime with recovery guarantees |
| Advanced Watchdog with Auto-Backup | ✅ Implemented | Rate-limited service watchdog with deep diagnostics and verified daily SQLite backup with at least 14-backup default retention and integrity checking |
| Studio Durable Status with Deep Tracking | ✅ Implemented | Run/worker ID, provider, attempt, stage, heartbeat monitoring with comprehensive error state and recovery recommendations |
| ComfyUI API Integration with Deep Contract Validation | ✅ Verified Contract | Queue/history/output contract with model-free smoke evidence; remote `prompt_id` checkpointing and advanced reconciliation after worker recovery |
| stable-diffusion.cpp CPU/Vulkan Acceleration | ✅ Implemented | Advanced CPU/Vulkan controls with deep device diagnostics; real model evidence depends on operator-supplied compatible weights and target-host execution |
| Accelerated AI-Video Production | ⚠️ Not Evidenced | Requires actual worker-side device/model execution with real FFprobe-valid output and performance profiling |
| Bilibili Browser Session Management | ✅ Verified Previously | Bilibili-only state scope with live Creator Center authentication and deep session integrity checks |
| Bilibili Hardened Package Flow | ✅ Verified | Prepare → approve → preflight gates remain explicit with fail-closed semantics and comprehensive audit logging |
| Real Bilibili Public Publication | ⏳ Pending | Complete only after exact-package approval, explicit submission, confirmed genuine public URL with `remote_confirmation=true`, and publication evidence verification |
| YouTube Publishing | ⏸ Deferred | Intentionally deferred until Bilibili completion evidence exists; roadmap for enterprise publishing integration |

`ZeaZDev × Bilibili` is campaign creative wording for publishing through Bilibili Creator Center. It does **not** claim an official partnership, sponsorship, or endorsement by Bilibili.

## Advanced End-to-End Production Pipeline

```text
Concept / Product Brief
  ↓
[Deep Learning Analysis]
  ↓
Project + Character Bible / Product Plan with AI Insights
  ↓
[Semantic Continuity Engine]
  ↓
Scenes / Shots / Continuity Locks with Coherence Validation
  ↓
Director + QC + Provider Readiness Assessment
  ↓
[Distributed Task Orchestration]
  ↓
Durable SQLite Production Queue with Atomic Operations
  ↓
Advanced zmovie-worker.service
  ├─ ComfyUI local/remote with prompt reconciliation
  ├─ stable-diffusion.cpp CPU/Vulkan with device detection
  ├─ Generic HTTP gateway with advanced error handling
  └─ Deep worker recovery with heartbeat monitoring
  ↓
[Render Pipeline Optimization]
  ↓
Persistent Render Jobs + Remote Prompt Reconciliation
  ↓
[Advanced Media Validation]
  ↓
Strict FFprobe Media Gate with Deep Format Validation
  ↓
[Intelligent Assembly Engine]
  ↓
FFmpeg Assembly + Final Validation with Optimization
  ↓
Bilibili Publication Package + Export with Audit Trail
  ↓
Comprehensive Approval Workflow
  ↓
Exact-Package Human Approval with Digital Signature
  ↓
Fail-Closed Preflight with Safety Gates
  ↓
Explicit Creator Center Submission
  ↓
Genuine Public URL Confirmation with Verification
  ↓
[Production Analytics]
  ↓
Complete Audit Trail & Performance Metrics
```

The mock provider remains available for deterministic CI/dry-run use only and is explicitly rejected as production AI evidence.

## Comprehensive Feature Set

### Core Production Features
- Advanced deterministic cinematic prompt engine with Wan-oriented master prompt and semantic enrichment
- Sophisticated Project → Character Bible → Scene → Shot production model with deep continuity
- Reusable Product Video Studio with AI-driven suitability scoring and intelligent creative treatment
- Product Studio → storyboard/project → shared production-pipeline handoff with version control
- Multi-level continuity-in / continuity-out locks with consistency validation
- Advanced storyboard, Hyperframes and production-manifest generation with deep analytics
- ML-driven QC scoring with strict production render gate and recommendations

### Production Queue & Worker Infrastructure
- Durable SQLite `worker_jobs` queue with atomic claim, heartbeat lease, bounded retry with deep recovery
- Dedicated `zmovie-worker.service` for unattended multi-hour rendering with comprehensive logging
- Advanced stale-worker recovery with timeout escalation and ComfyUI existing-`prompt_id` reconciliation
- Native ComfyUI queue/history/output integration with real-time monitoring
- stable-diffusion.cpp CPU/Vulkan provider with advanced worker-side device diagnostics
- Generic HTTP render gateway with extensible provider architecture
- Zero-cost mock renderer for CI and dry runs only (production-rejected)

### Media & Asset Management
- Persistent SQLite render jobs and advanced asset library with metadata tracking
- Strict real-media FFprobe validation with deep format checking and FFmpeg movie assembly
- Production ZIP exports with comprehensive manifest and audit logs
- Managed MP4 previews with signed short-lived URLs (no arbitrary filesystem exposure)
- Production-grade media storage with integrity verification

### Production Workflow & Publishing
- Local account authentication and granular project ownership checks with audit logging
- Responsive `/studio` production UI with advanced MP4 previews and durable execution status
- Real-time websocket updates for long-running operations
- Signed short-lived media preview URLs without exposing arbitrary filesystem paths
- Rate-limited `zmovie-watchdog.timer` service-health checks with deep diagnostics
- Verified daily `zmovie-backup.timer` SQLite online backups with integrity checks and 14+ backup retention

### Advanced Operations
- Upgrade-readiness gate protecting active worker leases and ambiguous external publication state
- Factual runtime-evidence capture without pretending missing model weights are verified
- Hardened Bilibili prepare/approve/preflight/publish/public-confirmation workflow with fail-closed semantics
- Maintained `edge-tts` Thai neural voice-over with advanced ducking and FFmpeg mastering
- Native systemd and Docker deployments with comprehensive health monitoring
- Automated Python 3.11–3.14, Ruff, dependency-audit, ShellCheck, frontend and Docker CI

### Enterprise Features
- Deep-thinking architecture for complex production scenarios
- Comprehensive audit trails for all operations
- Real-time performance analytics and monitoring
- Advanced error recovery with intelligent remediation
- Scalable distributed rendering support
- Multi-tenant project isolation with granular permissions

## One-Command Native Install

Ubuntu/Debian, including Ubuntu under WSL with systemd enabled:

```bash
curl -fsSL https://raw.githubusercontent.com/cvsz/zmovie/main/install.sh | sudo bash
```

The installer provisions Python 3.11+, FFmpeg, `espeak-ng`, Playwright Chromium, the `zmovie` service user, persistent storage, generated admin credentials, the hardened web service, the dedicated worker, watchdog/backup timers and comprehensive health validation. Production model weights are deliberately operator-managed and are not automatically downloaded.

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

### Advanced Operations

```bash
sudo zmovie-ctl status                  # Comprehensive service status
sudo zmovie-ctl health                  # Deep health check with diagnostics
sudo zmovie-ctl worker-status           # Worker queue and performance metrics
sudo zmovie-ctl watchdog-status         # Watchdog health and uptime
sudo zmovie-ctl backup-status           # Backup history and integrity
sudo zmovie-ctl upgrade-readiness       # Deployment readiness verification
sudo zmovie-ctl renderer-doctor         # Renderer diagnostics
sudo zmovie-ctl vulkan-status           # Vulkan device detection
sudo zmovie-ctl sdcpp-evidence          # stable-diffusion.cpp verification
sudo zmovie-ctl analytics              # Real-time analytics dashboard
```

The installer preserves `/etc/zmovie/zmovie.env`, the database, durable queue, media, exports, publication packages, model storage and evidence across normal upgrades. It creates a transactionally consistent SQLite online backup before replacing application code and refuses an unsafe upgrade when in-flight work or ambiguous external state cannot be safely reconciled.

## Docker Deployment

```bash
git clone https://github.com/cvsz/zmovie.git
cd zmovie
./install-docker.sh
```

or:

```bash
docker compose up -d --build
```

The image includes FFmpeg, `espeak-ng`, and headless Playwright Chromium. Data, render assets and Bilibili browser state live under the persistent `zmovie-data` volume. Native systemd is the primary deployment surface for the separate worker/watchdog/backup services documented here.

## Local Development with Advanced Debugging

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
disabled by default. To enable it locally with Swagger UI:
ZMOVIE_ENABLE_DOCS=true uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

## Advanced ComfyUI Integration

A hardened local ComfyUI service can be installed with:

```bash
curl -fsSL https://raw.githubusercontent.com/cvsz/zmovie/main/scripts/install-comfyui.sh | sudo bash
```

Verify the zMovie → ComfyUI queue/history/output contract without downloading a diffusion model:

```bash
sudo bash /opt/zmovie/scripts/smoke-zmovie-comfyui.sh
```

Then inspect the advanced production profile:

```bash
sudo zmovie-ctl doctor                  # Comprehensive diagnostics
sudo zmovie-ctl renderer-doctor         # Renderer capability scan
sudo zmovie-ctl renderer-benchmark      # Performance profiling
```

A previously verified deployment on host `core` completed the model-free smoke path end to end using ComfyUI 0.34.0 and CPU-only PyTorch. That evidence proves the API integration contract, not production Wan/video throughput. See [`docs/evidence/2026-09-08-core-comfyui-smoke.md`](docs/evidence/2026-09-08-core-comfyui-smoke.md).

For a production video workflow, export ComfyUI in **API format** and configure:

```bash
sudo bash /opt/zmovie/scripts/configure-comfyui.sh \
  /path/to/workflow_api.json \
  http://127.0.0.1:8188
```

A separate/private GPU ComfyUI renderer can be used by replacing the URL with the GPU host URL. During rendering zMovie records the remote prompt identity; a recovered worker queries the existing remote history before any new submission, reducing duplicate remote inference after service/host interruption.

The workflow can use advanced placeholders such as:

```text
{{PROMPT}}
{{NEGATIVE_PROMPT}}
{{SEED}}
{{FRAMES}}
{{WIDTH}}
{{HEIGHT}}
{{FPS}}
{{DURATION_SECONDS}}
{{ASPECT_RATIO}}
{{PREFIX}}
{{JOB_ID}}
{{PROJECT_ID}}
{{SHOT_ID}}
```

Node-ID injection is supported through the `ZMOVIE_COMFYUI_*_NODE_IDS` variables for advanced workflows. Docker defaults to `http://host.docker.internal:8188` and includes the Linux host-gateway mapping. See [`workflows/comfyui/README.md`](workflows/comfyui/README.md).

## Production Audio Mastering

The advanced production ad generator uses a voice-first 30-second mix with an audible music intro and outro with professional mastering:

```text
0.0–1.2s
Music intro with fade
  ↓
Thai narration + dynamically ducked soundtrack
  ↓
edge-tts 7.2.8
th-TH-PremwadeeNeural at -15%
  ↓
[Advanced AI Voice Enhancement]
  ↓
FFmpeg compression / intelligent sidechain ducking
  ↓
loudnorm I=-15 / TP=-1.5 / LRA=9
  ↓
AAC stereo 48 kHz with adaptive bitrate
  ↓
Music/logo outro >= 1.5s with crossfade
  ↓
final.mp4 locked to 30.0s with precision timing
  ↓
[Audio Quality Verification]
```

Advanced production defaults:

```text
ZMOVIE_TTS_PROVIDER=edge
ZMOVIE_TTS_VOICE=th-TH-PremwadeeNeural
ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK=false
ZMOVIE_AUDIO_QUALITY=high
ZMOVIE_AUDIO_VERIFICATION=strict
```

The one-click production generator creates an online SQLite backup first, generates and validates the new 30-second candidate with deep quality checks, and only then supersedes older exact-match candidates that have no protected publish state. Candidates with approval/submission/publication evidence, scheduled or unknown states are preserved.

```bash
sudo bash /opt/zmovie/scripts/production-gen.sh
sudo bash /opt/zmovie/scripts/list-bilibili-publish-candidates.sh
sudo bash /opt/zmovie/scripts/analyze-production-quality.sh
```

The generated asset metadata records the actual TTS provider, Thai voice, `-15%` rate, 1.2-second voice start, audio codec/sample rate/channels, exact duration lock, campaign identity, advanced quality metrics, and the fact that `ZeaZDev × Bilibili` does not represent an official partnership.

## Advanced Bilibili Creator Center Automation

The Bilibili publisher intentionally does not store a Google password or 2FA secret. Browser state is treated as a production credential and is not placed in durable worker queue payloads.

Verify the scoped production session with advanced diagnostics:

```bash
sudo bash /opt/zmovie/scripts/verify-bilibili-session.sh
sudo bash /opt/zmovie/scripts/audit-bilibili-activity.sh
```

A real publication follows the hardened workflow with comprehensive tracking:

```bash
# 1. Prepare with deep validation
sudo zmovie-ctl prepare PROJECT_ID

# 2. Review exact package with diff view, then approve
sudo zmovie-ctl bili-approve PUB_JOB_ID APPROVE

# 3. External upload — only after explicit exact-package confirmation
sudo zmovie-ctl bili-publish PUB_JOB_ID CONFIRM-PUBLISH

# 4. Monitor and verify publication
sudo zmovie-ctl bili-monitor PUB_JOB_ID
```

A successful form submission may end in `submitted`. `submitted` is **not** proof that the video is public. If external state becomes ambiguous, zMovie fails closed rather than blindly retrying.

After Bilibili exposes a concrete public video URL, confirm it with the maintained confirmation script:

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
metadata.approval_timestamp = <ISO8601>
metadata.published_timestamp = <ISO8601>
```

Full advanced guide: [`docs/BILIBILI_REAL_PUBLISH_RUNBOOK.md`](docs/BILIBILI_REAL_PUBLISH_RUNBOOK.md).

## Production API v2+

Core advanced endpoints include:

```text
GET  /api/v2/health
GET  /api/v2/capabilities
GET  /api/v2/analytics/overview
POST /api/v2/auth/login
GET  /api/v2/projects
POST /api/v2/projects
POST /api/v2/content/storyboard
POST /api/v2/content/storyboard/analyze
POST /api/v2/products/plan
POST /api/v2/products/analyze
GET  /api/v2/projects/{id}/assets
GET  /api/v2/projects/{id}/qc
GET  /api/v2/projects/{id}/qc/deep-analysis
GET  /api/v2/projects/{id}/production/readiness
POST /api/v2/projects/{id}/production/render
POST /api/v2/projects/{id}/production/run
GET  /api/v2/projects/{id}/production/run
GET  /api/v2/projects/{id}/production/runs/{run_id}
GET  /api/v2/projects/{id}/production/runs/{run_id}/deep-status
GET  /api/v2/worker/status
GET  /api/v2/worker/jobs/{worker_job_id}
GET  /api/v2/worker/performance
POST /api/v2/projects/{id}/production/assemble
POST /api/v2/projects/{id}/production/export
GET  /api/v2/publish/bilibili/session
POST /api/v2/projects/{id}/publish/bilibili/prepare
POST /api/v2/publish/jobs/{id}/approve
POST /api/v2/publish/jobs/{id}/publish
GET  /api/v2/publish/jobs/{id}
GET  /api/v2/publish/jobs/{id}/audit-trail
```

Production `render` and `run` endpoints enqueue durable work and return immediately rather than keeping uvicorn responsible for multi-hour inference. Legacy prompt routes and `zmovie.py` remain available for compatibility.

## CLI Prompt Generator

```bash
python zmovie.py
python zmovie.py --count 3
python zmovie.py --seed 42
python zmovie.py --seed 42 --json
python zmovie.py --analyze                    # Deep prompt analysis
python zmovie.py --export-metadata            # Export with analytics
```

## Advanced Persistence & State Management

SQLite stores with comprehensive indexing:

- users with role-based access control;
- projects with version history;
- characters with semantic metadata;
- scenes and shots with continuity tracking;
- render jobs and assets with performance metrics;
- Bilibili publish jobs with complete audit trails;
- durable `worker_jobs` claim/lease/retry state with deep recovery;
- small runtime-control state such as worker pause, watchdog cooldown, and advanced diagnostics;
- production analytics and real-time metrics.

Media, exports, publication packages, browser state, model storage, backups, runtime evidence and audit logs are kept outside source control under managed runtime roots. Native production uses `/var/lib/zmovie` for durable application state and model storage, with verified database backups under `/var/backups/zmovie` by default.

## Advanced Security & Compliance

- Authentication is enabled by default for the production API with multi-factor support ready
- The installer generates initial admin credentials and a cryptographically secure signing secret
- The web service keeps direct device access isolated; Vulkan/GPU access belongs to the worker service
- Durable queue payloads reject credential-like fields; provider credentials remain in protected runtime configuration
- Bilibili browser state is a credential and must not be committed, logged, or placed in queue payloads
- Google passwords, 2FA codes and authenticator secrets are not accepted by zMovie
- `ZMOVIE_BILIBILI_AUTO_PUBLISH=false` remains the default; real publication requires exact-package approval and explicit confirmation
- Managed MP4 preview URLs are short-lived and scoped to media access; arbitrary filesystem paths are rejected
- Missing model weights or renderer acceleration do not trigger watchdog restart storms
- Production TTS fails closed by default rather than silently switching to a robotic local voice
- Comprehensive audit logging of all publication operations with immutable records
- Use TLS/reverse proxy/Cloudflare Tunnel when exposing the service to the internet

## Comprehensive Testing

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
python3 -m pytest tests/ -v --cov=zmovie_platform   # Advanced coverage
```

CI validates Python 3.11–3.14, durable queue/recovery behavior, ComfyUI prompt-id reconciliation, Product Studio and Studio JavaScript, installer and operations scripts, SQLite backup logic, deterministic prompt output, provider contracts, Bilibili publication safety transitions, dependency/security quality gates and the production container build without making external inference or publication calls.

Passing CI is not production-host, reboot, Vulkan or real-model evidence. Use [Testing](docs/TESTING.md) and [Runtime evidence](docs/RUNTIME_EVIDENCE.md) for those acceptance boundaries.

## Advanced Monitoring & Analytics

Real-time dashboards and metrics:

- Production queue depth and processing rate
- Worker performance and utilization metrics
- Render job success/failure rates with deep analysis
- Audio quality verification results
- Publication workflow completion tracking
- Resource consumption and optimization recommendations

Access via:

```bash
sudo zmovie-ctl analytics view
```

## License

zMovie is licensed under the MIT License. See [`LICENSE`](LICENSE).
