# zMovie Completion and Security Remediation

**Date:** 2026-09-09
**Status:** Approved implementation scope

## Scope

This change closes the repository-owned security and completion gaps found during the zMovie audit:

- protect the legacy mutation and history endpoints when authentication is enabled while retaining their API paths;
- redirect the legacy root page to the authenticated Studio surface;
- replace the source-controlled authentication fallback with a process-ephemeral secret;
- rate-limit login, bootstrap, and legacy generation requests;
- return a safe public health projection instead of server filesystem paths and renderer configuration;
- reject asset registrations outside managed media/export/publish/object roots;
- remove server-local file paths from publisher API responses;
- upgrade the vulnerable FastAPI/Starlette dependency set and add reproducible dependency/security gates;
- fix shell validation findings, JavaScript syntax coverage, and stale entry-point/API documentation.

## Decisions

Authentication remains enabled by default. Operators who omit `ZMOVIE_SECRET_KEY` receive a random process-local signing key, so an accidental default deployment cannot use a known token; persistent deployments must still configure a generated secret. The legacy API remains available for compatibility, but its state-changing and history endpoints require an admin bearer token whenever authentication is enabled.

The public liveness endpoint exposes only aggregate status and version information. Detailed paths, probe data, and renderer configuration remain available to internal callers and CLI diagnostics. Registered asset paths are resolved against the managed roots before persistence, including symlink resolution.

API documentation is disabled by default and can be enabled explicitly for local or controlled environments with `ZMOVIE_ENABLE_DOCS=true`. No historic Git commit will be rewritten; every commit created by this task will be signed with the configured GPG key.

## Non-goals and external gates

This task does not invent credentials or claim completion for external integrations that cannot be proven locally. Real accelerated ComfyUI video generation, real FFmpeg assembly from AI output, a non-mock Bilibili upload with a confirmed public URL, durable published-state verification, and disabling Chrome remote debugging remain explicit deployment/acceptance gates when their required services and credentials are available.

## Acceptance criteria

1. Regression tests cover the auth guards, rate limits, safe health response, managed asset paths, secret fallback, and docs default.
2. The isolated test environment passes the full test suite, dependency audit, focused Ruff checks, shell syntax/ShellCheck, JavaScript syntax checks, and Compose validation.
3. The working tree contains no unintended user files or secrets.
4. New commits verify as good GPG signatures and `origin/main` reaches the pushed HEAD without force-updating history.
