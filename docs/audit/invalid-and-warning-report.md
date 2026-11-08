# Invalid and Warning Report — cvsz/zmovie

## Scope

Checked for invalid configuration, warnings, deprecated APIs, unsafe defaults, and anything that would cause CI or startup to fail.

## Invalid configuration

None found.

- `.env.example` is consistent with `config.py validate_runtime_settings()` (validated by `scripts/validate_repo.py`).
- `docker compose config --quiet` passes.
- Dockerfile builds (`docker compose build` exit 0).
- `python:3.15-slim` base image pull and build succeed.

## Warnings

- `ruff format --check` reports 99 files would be reformatted under ruff 0.17.1 (installed locally). CI pins `ruff==0.16.1` and `ruff check` passes; the format diffs are version-drift style wraps (e.g. long comprehension wrapping), not defects. Not reformatted to keep the diff minimal and aligned with the CI-pinned tool version.
- `python3 -m ruff check` exit 0 — no lint warnings.

## Deprecated APIs

None detected in the Python source tree under the ruff rule set. `playwright>=1.63.0,<2` is current; no deprecated FastAPI/Starlette APIs in use.

## Unsafe defaults

- `ZMOVIE_AUTH_ENABLED` defaults to `true` (auth on by default).
- `ZMOVIE_BILIBILI_AUTO_PUBLISH=false` default (no auto-publish).
- `ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK=false` default (TTS fails closed rather than switching to a local voice).
- `ZMOVIE_ENABLE_DOCS` defaults disabled.
- `ZMOVIE_HOST` defaults to `127.0.0.1` (loopback); `validate_runtime_settings()` rejects non-loopback bind without auth and a >=32-char secret.

## Status

No invalid configuration or actionable warnings remain. The ruff-format version drift is documented as an accepted warning (CI-pinned ruff 0.16.1 governs CI; local ruff 0.17.1 format drift is not a defect).
