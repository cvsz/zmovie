# ZeaZFlow N2N Image-to-Video Release

ZeaZFlow adds a provider-neutral image-to-video contract on top of the existing zMovie ComfyUI provider. It keeps zMovie independent from individual ComfyUI node IDs while still using ComfyUI as the first execution runtime.

## Release scope

The first release path supports:

- local or remote self-hosted ComfyUI
- explicit source-image upload through `/upload/image`
- `{{INPUT_IMAGE}}` / `{{SOURCE_IMAGE}}` workflow placeholders
- fallback binding to `LoadImage` nodes or `ZMOVIE_COMFYUI_IMAGE_NODE_IDS`
- existing zMovie prompt, seed, size, frame and output handling
- 9:16, 16:9, 1:1 and 21:9 output contracts
- 5, 10 and 20 second jobs
- three Lenovo LOQ 15ARP10E campaign variants
- fail-closed behavior when the source image is not actually connected to the workflow
- fail-closed behavior when ComfyUI returns no video output
- output manifest generation

## ComfyUI workflow preparation

Export the desired Wan/image-to-video workflow using ComfyUI's API-format export. The workflow must produce a video file and must have one source image input.

Preferred binding:

```json
{
  "12": {
    "class_type": "LoadImage",
    "inputs": {
      "image": "{{INPUT_IMAGE}}"
    },
    "_meta": {
      "title": "Source Image"
    }
  }
}
```

Alternatively set the LoadImage node ID explicitly:

```bash
export ZMOVIE_COMFYUI_IMAGE_NODE_IDS=12
```

The existing provider placeholders remain available: `{{PROMPT}}`, `{{NEGATIVE_PROMPT}}`, `{{SEED}}`, `{{WIDTH}}`, `{{HEIGHT}}`, `{{FRAMES}}`, `{{FPS}}`, `{{DURATION_SECONDS}}`, `{{ASPECT_RATIO}}`, `{{PREFIX}}`, `{{JOB_ID}}`, `{{PROJECT_ID}}`, and `{{SHOT_ID}}`.

## Runtime configuration

```bash
cp .env.example .env
export ZMOVIE_COMFYUI_URL=http://127.0.0.1:8188
export ZMOVIE_COMFYUI_WORKFLOW=/absolute/path/to/wan-i2v-api.json
```

If ComfyUI is protected by a bearer token or reverse proxy headers, use the existing `ZMOVIE_COMFYUI_TOKEN` and `ZMOVIE_COMFYUI_HEADERS_JSON` variables.

## Render three 9:16 product videos

```bash
python scripts/zflow_i2v.py /absolute/path/to/lenovo-loq.png \
  --count 3 \
  --duration 5 \
  --aspect-ratio 9:16 \
  --price-mode discount10
```

Outputs are written below `data/zflow/lenovo-loq/` and a `manifest.json` records every rendered variant.

For the non-discount campaign use:

```bash
python scripts/zflow_i2v.py /absolute/path/to/lenovo-loq.png --count 3 --price-mode full
```

The discount prompt uses the exact arithmetic result of 10% off THB 34,990: THB 31,491, and explicitly requires merchant authorization before that campaign claim is published.

## Release verification

The GitHub Actions test workflow must pass after this branch is merged. Local verification can be run with the repository's normal test command plus a live ComfyUI smoke render using a known-good exported I2V workflow.

A release is considered **code-verified** when CI, tests, quality checks and Docker build pass. It is considered **renderer-verified** only after a real ComfyUI/Wan job uploads an actual source image and returns a playable video artifact. Do not conflate these two gates.

## Architecture boundary

`ZFlowI2VJob` is the stable job contract. `ZFlowComfyUIProvider` is only the initial adapter. Future Wan-native, Diffusers, remote-GPU, or managed-provider adapters can implement the same contract without changing product campaign code.
