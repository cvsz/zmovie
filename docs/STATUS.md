# zMovie status vocabulary

This page defines the status words used by the README, operator guides, issue
templates, and evidence records. A status describes the strength of the
available evidence, not the ambition of a feature.

## Status definitions

| Status | Meaning | What it does not prove |
| --- | --- | --- |
| Implemented | Repository code and a documented path exist. | Runtime availability or production throughput. |
| Verified | A named local, CI, or runtime check passed for the stated scope. | Unchecked integrations or a different deployment. |
| Configured | Required settings or paths are present. | Valid provider output or safe publication. |
| Render-ready | Renderer reachability/configuration and media prerequisites pass. | AI-video quality, throughput, or every shot succeeding. |
| Production-ready | The stated production gates pass for the target workflow and environment. | Unrelated providers or external platform publication. |
| Pending | A required gate or confirmation has not happened yet. | Failure; the evidence is incomplete. |
| Submitted | An external upload request was accepted for processing. | A public URL or durable publication. |
| Published | The application records a published state. | Public reachability unless remote confirmation also exists. |
| Remotely confirmed | A public URL was probed and bound to the durable publication record. | Continued availability after the probe. |
| Deferred | Work is intentionally out of the current scope or sequencing. | A hidden implementation. |

## Current project boundary

The current repository evidence supports these statements:

- The native zMovie service and public Studio route are documented as verified
  deployment evidence; see [README](../README.md) and the
  [Cloudflare ingress evidence](evidence/2026-09-09-cloudflare-public-ingress.md).
- The ComfyUI queue/history/output contract and project assembly path have
  verified smoke evidence, but model-free smoke output is not accelerated
  AI-video production evidence.
- The stable-diffusion.cpp provider and CPU/Vulkan controls are implemented;
  real model throughput still depends on operator-supplied compatible weights
  and hardware.
- Bilibili package preparation, approval, and preflight are implemented and
  tested. Real public publication remains pending until a public URL and
  `remote_confirmation=true` are recorded.
- YouTube publishing is intentionally deferred; see the
  [YouTube roadmap](YOUTUBE_ROADMAP.md).
- The UI is currently English-only. The rules for future localization are
  specified in [I18N](I18N.md), not represented as an implemented feature.

## Evidence rule

Every status claim should identify its scope, date or commit when relevant,
verification command or observation, and boundary. A passing unit test,
configuration file, generated brief, or documentation statement is not by
itself runtime, interoperability, certification, or public-publication proof.
