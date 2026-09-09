# zMovie architecture

zMovie is a self-hosted production control plane. It turns a creative brief
into a project, character and scene continuity, render jobs, validated media,
an assembled movie, and an approval-gated publication package.

## Runtime entry points

`main:app` is the composed ASGI entry point for the application. It serves the
static legacy prompt surface, the Studio UI, the authenticated `/api/v2`
production API, media previews, and publisher routes. `app.py` retains the
legacy prompt implementation, while `zmovie.py` remains a compatible standalone
prompt generator.

The supported deployment surfaces are:

| Surface | Responsibility | Persistent state |
| --- | --- | --- |
| Native systemd | Production service, CLI, health, and operator workflows. | Config and database under the native service paths. |
| Docker Compose | Portable API/container deployment. | The `zmovie-data` volume. |
| Local development | Direct ASGI/API and Studio iteration. | Repository-local development data when configured. |

Use [Configuration](CONFIGURATION.md) for path and environment precedence and
[Operations](OPERATIONS.md) for lifecycle commands.

## Request and data flow

```text
browser or CLI
  -> main:app
  -> authentication and project ownership
  -> v2 project/storyboard/QC state
  -> provider adapter and persistent render job
  -> managed media registration and ffprobe validation
  -> FFmpeg assembly and final-media validation
  -> Bilibili package preparation
  -> human approval and fail-closed preflight
  -> one external submission attempt
  -> public URL confirmation
```

The legacy single-prompt routes remain for compatibility. New production
workflows should use the v2 project and pipeline contracts described in the
[API guide](API.md).

## Domain and persistence

The platform package owns project, character-bible, scene, shot, render-job,
asset, QC, export, authentication, and publisher state. SQLite is the default
durable store. Native deployments keep application data under the configured
service data root; Docker deployments use the persistent volume.

Managed media, exports, publication packages, and browser state are separate
from source-controlled code. Asset registration resolves paths against managed
roots and rejects escapes, including symlink escapes. Preview URLs are signed,
short-lived, and limited to managed MP4 assets.

## Provider boundary

The renderer abstraction supports:

- ComfyUI API workflows for local or private/remote renderers;
- the stable-diffusion.cpp provider with explicit model and video-readiness
  gates;
- generic HTTP/webhook integration where configured; and
- the mock provider for deterministic dry runs and tests only.

Provider configuration is not output evidence. Every production shot must
produce managed media that passes extension, `ffprobe`, stream, duration, and
dimension checks before assembly. See the
[status vocabulary](STATUS.md) and [renderer guides](INDEX.md).

## Publication boundary

Production orchestration stops at a human approval gate. Bilibili preparation,
approval, preflight, submission, and public confirmation are separate durable
states. `submitted` is not `published`, and `published` is not remotely
confirmed until a public URL is probed and bound to the job.

The publisher intentionally uses scoped browser state and does not accept or
store a Google password, recovery code, authenticator secret, or 2FA code. See
[Bilibili publishing](BILIBILI_PUBLISHING.md) and [Security](../SECURITY.md).

## Security boundaries

Authentication, project ownership, managed roots, rate limits, approval
binding, idempotency, public-health redaction, and fail-closed publication are
part of the architecture. Public ingress through a tunnel or reverse proxy
does not remove the need for application authentication and route review.
