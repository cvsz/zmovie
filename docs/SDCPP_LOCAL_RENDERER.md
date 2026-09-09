# stable-diffusion.cpp local renderer for zMovie

This integration gives zMovie a local text-to-video provider that can run without CUDA.
It uses `stable-diffusion.cpp` and preserves zMovie's production safety boundary:
configuration readiness is not publication evidence. Every generated clip must still pass
zMovie's ffprobe video validation before assembly, Bilibili preparation, or export.

## Architecture

```text
zMovie renderer router
  ├─ comfyui       accelerated/API workflow path
  ├─ sdcpp         stable-diffusion.cpp: Vulkan/iGPU -> CPU fallback
  ├─ webhook       remote/self-hosted video gateway
  └─ mock          dry-run only; rejected by production routes
```

For `sdcpp`, the default backend is `auto`. zMovie omits an explicit upstream
`--backend` assignment in this mode so stable-diffusion.cpp can use its automatic
GPU -> integrated GPU -> CPU preference and auto-fit planner. Operators can force
`cpu` or a device such as `vulkan0` when required.

## 1. Deploy current zMovie

```bash
cd ~/zmovie
git pull
sudo bash ./install.sh upgrade
```

## 2. Install the inference engine

Automatic Vulkan build with CPU build fallback:

```bash
sudo zmovie-ctl sdcpp-install auto
```

Or from the repository:

```bash
make sdcpp-install SDCPP_BACKEND=auto
```

The installer builds the official `leejet/stable-diffusion.cpp` source and installs
`/usr/local/bin/sd-cli`. It does **not** download model weights.

Inspect devices:

```bash
sd-cli --list-devices
sudo zmovie-ctl sdcpp-status
sudo zmovie-ctl doctor
```

At this point `cli_available` may be true while `production_ready` remains false.
That is expected until a real video model bundle is configured.

## 3. Configure an operator-supplied video model

At least one of `--model` or `--diffusion-model` is required. Add whichever
text encoder/VAE/model components are required by the selected upstream model.
All configured files must be readable by the `zmovie` service account.

Example skeleton:

```bash
sudo zmovie-ctl sdcpp-config \
  --diffusion-model /srv/models/video/model.gguf \
  --vae /srv/models/video/vae.safetensors \
  --t5xxl /srv/models/video/text-encoder.gguf \
  --backend auto \
  --fps 8 \
  --output-format avi
```

The configuration command explicitly sets `ZMOVIE_SDCPP_VIDEO_ENABLED=true` only
after validating the supplied paths. It never downloads weights automatically.

Supported configuration inputs include:

```text
ZMOVIE_SDCPP_CLI
ZMOVIE_SDCPP_BACKEND
ZMOVIE_SDCPP_VIDEO_ENABLED
ZMOVIE_SDCPP_MODEL
ZMOVIE_SDCPP_DIFFUSION_MODEL
ZMOVIE_SDCPP_HIGH_NOISE_DIFFUSION_MODEL
ZMOVIE_SDCPP_VAE
ZMOVIE_SDCPP_AUDIO_VAE
ZMOVIE_SDCPP_T5XXL
ZMOVIE_SDCPP_LLM
ZMOVIE_SDCPP_CLIP_VISION
ZMOVIE_SDCPP_EMBEDDINGS_CONNECTORS
ZMOVIE_SDCPP_PARAMS_BACKEND
ZMOVIE_SDCPP_MAX_VRAM
ZMOVIE_SDCPP_AUTO_FIT
ZMOVIE_SDCPP_EXTRA_ARGS_JSON
ZMOVIE_SDCPP_FPS
ZMOVIE_SDCPP_FRAME_MULTIPLE
ZMOVIE_SDCPP_FRAME_OFFSET
ZMOVIE_SDCPP_WIDTH
ZMOVIE_SDCPP_HEIGHT
ZMOVIE_SDCPP_OUTPUT_FORMAT
ZMOVIE_SDCPP_SEED
ZMOVIE_SDCPP_TIMEOUT
```

`ZMOVIE_SDCPP_EXTRA_ARGS_JSON` cannot override zMovie-controlled prompt, output,
mode, backend, auto-fit, dimensions, FPS, frame count, seed, parameter backend,
or VRAM budget flags.

## 4. Production readiness

```bash
sudo zmovie-ctl sdcpp-status
sudo zmovie-ctl providers
sudo zmovie-ctl doctor
```

A configured provider is allowed into the production router only after the engine,
model paths, explicit video enablement, FFmpeg, and ffprobe gates pass. The final
proof remains the generated media itself:

```text
real provider output
  -> managed path
  -> recognized video extension
  -> ffprobe succeeds
  -> video stream exists
  -> duration > 0
  -> width/height > 0
  -> production shot accepted
```

If any shot fails this gate, the one-click production run stops before assembly.

## 5. Run production

```bash
sudo zmovie-ctl readiness prj_xxx
sudo zmovie-ctl production prj_xxx sdcpp
```

Successful orchestration remains:

```text
render all real shots
  -> validate each clip
  -> strict FFmpeg assembly
  -> validate final movie
  -> prepare Bilibili package
  -> export ZIP + checksums
  -> STOP at human approval gate
```

The renderer integration does not auto-approve or auto-publish to Bilibili.
`submitted` is still not equivalent to `published`; publication completion requires
a confirmed public Bilibili URL and `remote_confirmation=true`.

## CPU and Vulkan expectations

CPU mode is a functional fallback, not a GPU emulator. Large diffusion-video models
can take substantially longer and may exceed available RAM. Vulkan can use a supported
integrated/discrete GPU without CUDA, but model compatibility and memory requirements
remain model-specific. Start with a short, low-resolution production smoke render and
only increase frame count/resolution after the real output passes zMovie media QC.
