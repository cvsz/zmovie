# Video Rendering Review — zMovie Enterprise Audit

**Baseline SHA:** `67023e1a5a4f69f5154ac19c58b5e390154f3d91`  
**Branch:** `feat/zmovie-enterprise-production-hardening`

## Summary

The media pipeline (ComfyUI remote GPU, stable-diffusion.cpp CPU/Vulkan, FFmpeg assembly, ffprobe validation) is implemented, but real-model render throughput and output integrity were **not verified** in this audit because they require operator-supplied model weights, a renderer/GPU environment, and real media. These must not be fabricated.

## Components

| Component | Status | Notes |
|-----------|--------|-------|
| ComfyUI remote GPU API integration | Implemented | Queue/history/output contract; remote `prompt_id` checkpointing and reconciliation after worker recovery |
| stable-diffusion.cpp CPU/Vulkan | Implemented | Device detection; production-ready gated on model/config |
| FFmpeg assembly + ffprobe gate | Implemented | `ffmpeg`/`ffprobe` presence checked in health; media pipeline includes FFprobe gate |
| Video worker / long-running render worker | Implemented | Isolated from uvicorn lifetime; `zmovie-worker.service` |
| GPU discovery / CUDA | Documented | CPU fallback available; GPU memory management operator-configured |
| Temp workspace cleanup | Implemented | Managed media/export/publish/object roots |
| Render determinism | Not evidenced | Requires real model run |
| A/V sync, subtitle sync | Not evidenced | Requires real render + ffprobe validation |

## Verification guidance

Do not assume success from FFmpeg exit code 0. Validate final output with `ffprobe` and integrity checks (codec, resolution, aspect ratio, frame rate, audio sample rate, A/V/subtitle sync). Test representative workflows without unauthorized copyrighted material.

## Residual risk

Real render determinism, GPU utilization, and media output integrity require operator execution on target infrastructure with real model weights.
