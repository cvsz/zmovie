# AGENTS.md

This file defines repository-wide operating rules for AI coding agents working on `cvsz/zmovie`.

## Mission

zMovie is a self-hosted AI movie and product-video production control plane. Preserve its core guarantees: durable execution, resumable rendering, strict media validation, explicit provider readiness, human approval for external publication, evidence-based status claims, and fail-closed behavior at security and production boundaries.

## Repository priorities

1. Never trade durability for convenience. Long-running rendering belongs in the durable worker queue, not in the web request lifecycle.
2. Never report production success from configuration, mocks, smoke tests, or CI alone. Production claims require the scope-specific evidence described in `docs/STATUS.md`.
3. Never bypass FFprobe/FFmpeg validation, project ownership, managed media-root protections, queue credential hygiene, publication approval, or public-confirmation gates.
4. Keep secrets out of source, job payloads, logs, docs, fixtures, screenshots, commits, and generated reports.
5. Prefer idempotent installers, transactional upgrades, bounded retries, resumable operations, and deterministic outputs.
6. Preserve compatibility with Python 3.11-3.14 and the supported native Ubuntu/Debian deployment path.

## Canonical production entry point

Use the Makefile as the operator-facing control surface. For a real project:

```bash
make production PROJECT_ID=prj_REAL PROVIDER=auto
```

On the DBC production host with the Windows SMB capacity tier required:

```bash
make production \
  PROJECT_ID=prj_REAL \
  PROVIDER=auto \
  SMB_MODE=required \
  SMB_MOUNT=/mnt/zmovie-storage
```

Do not silently substitute `mock` for a real provider. `mock` is test/dry-run only and must remain rejected by production routes.

## Provider contract

All provider changes must preserve the common contract in `zmovie_platform/providers.py`: provider identity/specification, supported modes, duration/aspect constraints, deterministic metadata handling where applicable, explicit configuration checks, bounded network/process timeouts, structured errors, and a result that can be reconciled with the persistent render job.

### Provider: ComfyUI (`comfyui`)

Purpose: primary self-hosted/local-or-remote workflow provider for text-to-video and image-to-video.

Agent rules:

- Preserve API-format workflow loading and placeholder/node binding.
- Never mark a smoke workflow as production-ready.
- Preserve remote `prompt_id` checkpointing and history reconciliation so worker restarts do not blindly resubmit work.
- Existing remote work must be reconciled before creating a replacement prompt.
- Treat endpoint, token, custom headers, workflow path, node IDs, dimensions, FPS, seed, and filename prefix as configuration, not hard-coded deployment facts.
- Download/register only outputs proven to belong to the reconciled prompt/job.
- Keep network calls bounded and fail clearly on HTTP, timeout, malformed JSON, missing history, execution error, or missing media output.
- For image-to-video, fail closed if the source image is not actually bound into the workflow.

Primary surfaces: `zmovie_platform/providers.py`, ComfyUI configuration/install scripts, `workflows/comfyui/`, renderer diagnostics, and provider tests.

### Provider: stable-diffusion.cpp (`sdcpp`)

Purpose: local CPU/Vulkan inference path without requiring CUDA.

Agent rules:

- Keep CPU as a first-class backend; do not assume NVIDIA/CUDA availability.
- Model weights remain operator-managed unless an explicit feature changes that policy.
- Validate required model components before claiming production readiness.
- Keep backend/device diagnostics separate from real-model evidence.
- Do not treat successful binary installation or Vulkan enumeration as proof that video generation works.
- Preserve bounded subprocess execution, output discovery, media validation, and evidence collection.
- On the DBC host, NVIDIA GeForce 210 is display-only and must not be treated as a modern ML accelerator.

Primary surfaces: sdcpp provider/runtime code, `scripts/install-sdcpp.sh`, `scripts/configure-sdcpp.sh`, `docs/SDCPP_LOCAL_RENDERER.md`, runtime diagnostics, and tests.

### Provider: Generic HTTP/Webhook (`webhook`)

Purpose: integration point for a remote/self-hosted rendering gateway, including Wan/Kling/Veo-style gateways when the operator supplies one.

Agent rules:

- Require `ZMOVIE_PROVIDER_WEBHOOK`; never invent an endpoint.
- Keep bearer/API credentials only in protected configuration/environment and out of persistent queue payloads.
- Validate URL scheme/response shape and use bounded timeouts.
- Do not log authorization headers or secret-bearing response bodies.
- Treat provider-specific capabilities as external contract data; do not fabricate support for duration, aspect ratio, image input, polling, callbacks, or cancellation.
- If asynchronous remote jobs are supported, persist the remote identifier and reconcile before retrying submission.
- Network failure must be retryable only where the durable queue policy allows it; never create unbounded retry loops.

Primary surfaces: `zmovie_platform/providers.py`, environment configuration, worker execution/retry handling, and provider tests.

### Provider: Mock (`mock`)

Purpose: deterministic CI, development, smoke, and dry-run behavior only.

Agent rules:

- Never promote mock output to production evidence.
- Keep production endpoints and `make production` fail-closed against mock.
- Mock output may exercise queue/media plumbing, but status language must state its limited scope.
- Keep mock deterministic enough for tests and avoid external dependencies beyond optional FFmpeg placeholder generation.

### Future providers

New providers must not be added as one-off shortcuts. Implement them behind the same provider abstraction and document:

- stable provider ID and name;
- text-to-video/image-to-video modes;
- supported durations and aspect ratios;
- required configuration and secret handling;
- synchronous vs asynchronous lifecycle;
- persistent remote-job reconciliation semantics;
- timeout/retry/cancellation behavior;
- output acquisition and strict media validation;
- production-readiness checks;
- unit/integration tests and operator documentation.

A provider is not production-ready merely because its class exists.

## Durable worker and queue rules

- API routes validate and enqueue; they must not perform multi-hour work inline.
- Queue state transitions must remain atomic and recoverable.
- Preserve leases, heartbeats, stale recovery, bounded retries, pause/resume, and terminal failure semantics.
- Queue payloads must never contain provider tokens, cookies, browser state, passwords, or SMB credentials.
- When adding a new long-running phase, make it resumable or explicitly restart-safe.
- Re-running a claimed/recovered job must not duplicate remote provider submissions when a remote identifier already exists.

## Media and assembly rules

- Never trust file extension alone. Real media must pass the existing FFprobe gate.
- Preserve managed-root and symlink/path-escape protections.
- Final assembly must remain reproducible and must fail on missing/invalid required shots.
- Do not weaken FFmpeg error handling to force a green run.
- A final MP4 is not evidenced unless the real artifact exists and passes the validation path.

## Product Video Studio rules

- Preserve claim-safe product treatment and suitability scoring.
- Do not invent benchmarks, FPS, discounts, scarcity, certifications, warranties, merchant authorization, or product capabilities.
- Handoff must use the shared project/storyboard/worker/provider pipeline rather than a separate ad-only execution path.

## SMB storage tier rules

The DBC layout uses local Linux storage for hot/active state and Windows SMB for capacity/archive data.

Keep local:

- SQLite databases and worker queue state;
- active model files required by the renderer;
- in-progress render workspace and temp/cache;
- files whose atomic local semantics are required during production.

SMB may hold completed source/media copies, final videos, exports, archives, backups, and evidence.

Rules:

- Never place active SQLite or in-progress render temp directly on SMB.
- Verify the configured mount is actually `cifs`/`smb3` before writing archival data.
- A disconnected/unmounted share must never degrade into writing silently to the local mount-point directory.
- Copy completed artifacts/evidence first, verify SHA-256, then apply any local cleanup policy.
- SMB failure must not destroy a successfully rendered local artifact; retain it for retry/archive recovery.
- Never commit SMB credentials. Use the protected credentials file/configuration described by the SMB runbook.

## Bilibili and external publishing

- Preparing a package is not publishing.
- Approval must refer to the exact package/job being submitted.
- External submission requires the existing explicit confirmation gate.
- Browser session/cookie state is sensitive configuration and must not enter Git or queue payloads.
- Never claim successful publication without remote confirmation and a genuine public URL.
- Do not expand to YouTube publishing unless the task explicitly changes the currently deferred sequencing.

## Security and privacy

- Do not weaken authentication, project ownership checks, signed preview URLs, rate limits, path validation, service isolation, or publication gates to simplify a feature.
- Never hard-code tokens/passwords/cookies/private keys.
- Redact secrets from exceptions and operator reports.
- Preserve `PrivateDevices=true` for the web service; renderer device access belongs to the worker when needed.
- Treat uploaded media and external-provider output as untrusted until validated.

## Status and evidence vocabulary

Use the repository's evidence discipline:

- `Implemented`: code/path exists.
- `Verified`: a named check passed for an explicitly stated scope.
- `Pending`/`Blocked`: required runtime/operator/external evidence is missing.

Do not convert CI success into host, model, GPU, publication, reboot, SMB, or real-media evidence.

## Testing requirements

Before considering a change complete, run the smallest relevant tests plus the repository quality suite when practical:

```bash
python -m compileall -q zmovie.py app.py main.py zmovie_platform tests
python -m unittest discover -s tests -v
python -m ruff check app.py main.py zmovie_platform tests
bash -n install.sh install-docker.sh scripts/*.sh
node --check static/app.js
node --check static/studio-preview.js
python scripts/verify_docs.py
```

Use `make check` where it covers the changed surface. Provider changes require focused provider tests. Shell changes require ShellCheck in CI. Docker-related changes require compose/build validation.

## Change discipline

- Read the current implementation before editing; do not infer stale architecture from old prompts or issues.
- Keep changes minimal and aligned with existing naming, error handling, and status semantics.
- Update canonical docs when operator behavior changes.
- Avoid generated/vendor/build output in commits.
- Never create a commit that only reformats unrelated files.
- Do not merge a production-impacting PR until exact-head CI is green.
- After merge, distinguish repository/CI completion from real-host acceptance.

## Provider review checklist

For every provider-related PR, verify all of the following before approval:

1. Provider ID/capabilities and production role are explicit.
2. Secrets are not persisted in queue payloads or logs.
3. Timeouts and failures are bounded and actionable.
4. Async remote identifiers are persisted/reconciled where applicable.
5. Retries cannot duplicate expensive remote work unintentionally.
6. Output is copied/registered only after ownership/job association is established.
7. Real output still passes the shared media validation gate.
8. Mock/smoke readiness cannot satisfy production readiness.
9. Worker restart/reboot semantics remain safe.
10. Tests and docs cover the provider-specific behavior and evidence boundary.
