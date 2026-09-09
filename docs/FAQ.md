# Frequently Asked Questions

## Is zMovie an AI model?

No. zMovie is a self-hosted production platform that coordinates story
development, shot planning, render providers, assembly, preview, and creator-
platform publication workflows. The platform can call ComfyUI, a generic HTTP
provider, or a local mock/dry-run provider.

## Does a mock render prove that accelerated video works?

No. A mock or model-free ComfyUI smoke test proves the queue/history/output
contract only. Real model throughput, GPU suitability, and production quality
require the relevant provider and hardware evidence. See
[`STATUS.md`](STATUS.md) and [`COMFYUI_REMOTE_GPU.md`](COMFYUI_REMOTE_GPU.md).

## Where should I start?

Use [`INDEX.md`](INDEX.md) to choose a path:

- users: [`CONFIGURATION.md`](CONFIGURATION.md) and the root
  [`README`](../README.md);
- operators: [`OPERATIONS.md`](OPERATIONS.md) and
  [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md);
- developers: [`ARCHITECTURE.md`](ARCHITECTURE.md), [`API.md`](API.md), and
  [`TESTING.md`](TESTING.md);
- release maintainers: [`RELEASE.md`](RELEASE.md) and
  [`STATUS.md`](STATUS.md).

## How do I use the local stable-diffusion.cpp renderer?

Read [`SDCPP_LOCAL_RENDERER.md`](SDCPP_LOCAL_RENDERER.md). It documents the
optional binary/model setup and the safety boundary around local rendering.
The renderer is not required for the core service or for the model-free smoke
tests.

## Does a submitted Bilibili job mean the video is public?

No. `submitted` means the external form submission completed. Public completion
requires a durable published state, a concrete public URL, and
`remote_confirmation=true`. Follow the
[`BILIBILI_REAL_PUBLISH_RUNBOOK.md`](BILIBILI_REAL_PUBLISH_RUNBOOK.md).

## Can zMovie accept my Google password or 2FA code?

No. Do not send Google passwords, one-time codes, authenticator secrets, or
browser cookies to zMovie. Use the provider's own authenticated browser flow
and keep browser state private. See [`SECURITY.md`](../SECURITY.md) and the
Bilibili runbook.

## Is the interface translated already?

The current UI is English-only. New user-facing text should follow the
catalog-ready rules in [`I18N.md`](I18N.md), including BCP 47 locale tags,
fallback behavior, interpolation, pluralization, and locale-aware formatting.

## Which deployment should I use?

Use the native systemd path when you need the documented host service and
managed state layout. Use Docker Compose for portable local or controlled
deployment workflows. [`OPERATIONS.md`](OPERATIONS.md) and
[`CONFIGURATION.md`](CONFIGURATION.md) describe the shared boundaries and
environment configuration.

## How do I report a security issue?

Follow [`SECURITY.md`](../SECURITY.md). Do not open a public issue containing
credentials, private URLs, browser state, or an exploit that exposes live
systems.
