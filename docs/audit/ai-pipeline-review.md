# AI Pipeline Review — zMovie Enterprise Audit

**Baseline SHA:** `67023e1a5a4f69f5154ac19c58b5e390154f3d91`  
**Branch:** `feat/zmovie-enterprise-production-hardening`

## Summary

The AI content factory (topic research, planning, script, storyboard, scene generation, visual assets, voice, music, composition, subtitles, thumbnails, metadata, human review, publishing, analytics) is architected around the durable SQLite queue and provider abstraction. Real-model inference was not executed in this audit.

## Provider abstraction

- `zmovie_platform/providers.py` defines provider specs; mock adapter available for CI/dry-run only (explicitly rejected as production evidence).
- ComfyUI and stable-diffusion.cpp providers are pluggable via config.
- Model configuration, prompt versioning, and provider failover follow the configured settings.

## State & recovery

- Content state machine transitions are validated in `studio_cinema.py` (forward-only states except retry from APPROVED).
- Job tracking, retries, dead-letter, and recovery handled by the worker queue (see worker-queue-review.md).
- Failed tasks recoverable via `recover_stale` and bounded retries.

## Residual risk

Prompt/model provenance, cost/usage tracking, and reproducibility require real-model runs and operator-managed model storage. These are not evidenced here.
