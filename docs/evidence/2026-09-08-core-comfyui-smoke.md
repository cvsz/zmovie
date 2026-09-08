# Verified Runtime Evidence — core / ComfyUI smoke

Date: 2026-09-08 UTC
Host: `core`
Scope: zMovie native systemd deployment → ComfyUI API → provider queue/history → output download

## Result

PASS.

Verified from operator-provided runtime output:

- zMovie native installation healthy on port 8080.
- ComfyUI service active on `127.0.0.1:8188`.
- ComfyUI version: `0.34.0`.
- Python: `3.14.4`.
- PyTorch: `2.14.0+cpu`.
- Device type: CPU.
- zMovie health reported:
  - `configured=true`
  - `reachable=true`
  - `workflow_valid=true`
  - `nodes_available=true`
  - `ready=true`
  - `render_ready=true`
  - `missing_node_types=[]`
- Model-free API workflow used only built-in `LoadImage` and `SaveImage` nodes.
- zMovie submitted the prompt through the ComfyUI provider, observed the history response, then downloaded the generated output through the ComfyUI API.
- Output persisted under `/var/lib/zmovie/media/comfyui-smoke/...png` with `zmovie:zmovie` ownership.

## Boundary of this evidence

This proves the local integration contract and production storage path. It does **not** prove a production diffusion-video model, a Wan render, GPU acceleration, throughput, or Bilibili publication.

Because the verified renderer is CPU-only, large diffusion-video workloads should not be marked production-ready from this smoke result. The recommended production topology is to retain zMovie on `core` and use a separate/private accelerated ComfyUI renderer when a GPU is available.

## Next evidence gates

1. Production video workflow validates with zero missing node types.
2. Real short-shot video render completes.
3. FFmpeg assembles a real rendered project.
4. Bilibili authenticated session is verified.
5. Controlled Bilibili test upload completes.
