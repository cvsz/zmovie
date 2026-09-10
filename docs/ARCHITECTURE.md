# zMovie architecture

zMovie is a self-hosted production control plane. It turns a creative brief
into a project, character and scene continuity, render jobs, validated media,
an assembled movie, and an approval-gated publication package.

## Runtime entry points

`main:app` is the composed ASGI entry point for the application. It serves the
static legacy prompt surface, the Studio UI, Product Studio, the authenticated
`/api/v2` production API, media previews, and publisher routes. `app.py` retains
the legacy prompt implementation, while `zmovie.py` remains a compatible
standalone prompt generator.

Long-running production execution is deliberately separated from the ASGI
process. The API validates and enqueues work in SQLite; `python -m
zmovie_platform.worker`, normally managed by `zmovie-worker.service`, claims
and executes durable production jobs. See [Long-running render worker](LONG_RUNNING_RENDER_WORKER.md).

The supported deployment surfaces are:

| Surface | Responsibility | Persistent state |
| --- | --- | --- |
| Native systemd | Hardened web/API, durable worker, watchdog/backup timers, CLI, health and operator workflows. | Config and database under the native service paths. |
| Docker Compose | Portable API/container deployment. | The `zmovie-data` volume. |
| Local development | Direct ASGI/API and Studio iteration. | Repository-local development data when configured. |

Use [Configuration](CONFIGURATION.md) for path and environment precedence and
[Operations](OPERATIONS.md) for lifecycle commands.

## Request and data flow

```text
browser / Product Studio / CLI
  -> main:app
  -> authentication + project ownership + QC/provider checks
  -> persistent production run
  -> durable SQLite worker_jobs queue
  -> zmovie-worker.service
       -> render provider
       -> real-media validation / ffprobe
       -> FFmpeg assembly
       -> Bilibili package preparation
       -> production export
  -> approval_required
  -> human exact-package approval
  -> fail-closed preflight
  -> one external submission attempt
  -> public URL confirmation
```

The web process never needs to own a multi-hour renderer child process. A web
restart therefore does not erase queued production state. Worker claims use
SQLite transactions, leases and heartbeats; stale jobs are reconciled on
worker startup. Product Studio generates a normal project and hands it to the
same production path instead of creating a second renderer stack.

The legacy single-prompt routes remain for compatibility. New production
workflows should use the v2 project and production contracts described in the
[API guide](API.md).

## Domain and persistence

The platform package owns project, character-bible, scene, shot, render-job,
asset, QC, export, authentication, publisher and durable worker state. SQLite
is the default durable store and uses WAL mode. Native deployments keep
application data under the configured service data root; Docker deployments use
the persistent volume.

`worker_jobs` stores only execution metadata and claim/retry state. Queue
payloads reject credential-like fields. Tokens, cookies and browser state must
remain in protected runtime configuration/state, not queue payload JSON.

Managed media, exports, publication packages, models, evidence and browser
state are separate from source-controlled code. Asset registration resolves
paths against managed roots and rejects escapes, including symlink escapes.
Preview URLs are signed, short-lived, and limited to managed MP4 assets.

## Provider boundary

The renderer abstraction supports:

- ComfyUI API workflows for local or private/remote renderers;
- the stable-diffusion.cpp provider with explicit model and video-readiness
  gates;
- generic HTTP/webhook integration where configured; and
- the mock provider for deterministic dry runs and tests only.

For ComfyUI, zMovie checkpoints the remote `prompt_id` after submission. If a
worker is interrupted, recovery first queries `/history/{prompt_id}` and
reconciles the existing remote execution rather than blindly submitting a
second prompt.

Provider configuration is not output evidence. Every production shot must
produce managed media that passes extension, `ffprobe`, stream, duration and
dimension checks before assembly. See the [status vocabulary](STATUS.md),
[Vulkan renderer](VULKAN_RENDERER.md) and [Runtime evidence](RUNTIME_EVIDENCE.md).

## Service isolation

The native web unit remains hardened and keeps `PrivateDevices=true`. Direct
render-device access belongs to `zmovie-worker.service`; the installer adds the
service user to existing `render`/`video` groups only when those groups exist.
Models are stored below `/var/lib/zmovie/models` so `ProtectHome=true` does not
force production weights into a user home directory.

The watchdog and backup timers are operational control-plane components, not
renderer-readiness gates. Missing model weights must not cause restart storms.
The watchdog can rate-limit repair of a demonstrably unhealthy web service or a
worker required by active durable work.

## Publication boundary

Production orchestration stops at a human approval gate. Bilibili preparation,
approval, preflight, submission, and public confirmation are separate durable
states. `submitted` is not `published`, and `published` is not remotely
confirmed until a public URL is probed and bound to the job.

The publisher intentionally uses scoped browser state and does not accept or
store a Google password, recovery code, authenticator secret, or 2FA code.
Ambiguous external state is never automatically retried. See [Bilibili publishing](BILIBILI_PUBLISHING.md)
and [Security](../SECURITY.md).

## Security boundaries

Authentication, project ownership, managed roots, rate limits, approval
binding, idempotency, public-health redaction, queue credential rejection,
worker privilege separation and fail-closed publication are part of the
architecture. Public ingress through a tunnel or reverse proxy does not remove
the need for application authentication and route review.
