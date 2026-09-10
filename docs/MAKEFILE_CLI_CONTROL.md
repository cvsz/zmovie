# zMovie Makefile + CLI Control Panel

zMovie ships with two operator interfaces for the full-stack installation:

- `Makefile` for repeatable installation, development, CI, Docker, renderer and production operations.
- `zmovie-ctl` for service control and production workflow operations on a native installation.

## Full-stack native install

From a repository checkout:

```bash
make server-packages
make full-stack
```

`make server-packages` installs the Ubuntu/Debian prerequisites shared by zMovie, ComfyUI and stable-diffusion.cpp: Python/venv tooling, FFmpeg, TTS support, build tooling, OpenGL runtime libraries and Vulkan development/diagnostic packages. `make full-stack` runs that target automatically, then provisions the application runtime, Python virtual environment, Playwright Chromium, systemd service, persistent data/config directories, health check and the global `/usr/local/bin/zmovie-ctl` command.

The native installer also installs `make` so subsequent upgrades and operator tasks can use the Makefile directly.

For an existing installation:

```bash
make upgrade
make status
make doctor
```

Durable worker and runtime checks:

```bash
make worker-status
make worker-jobs
make worker-recover
make watchdog-status
make backup-status
make renderer-doctor
make vulkan-status
make sdcpp-evidence
make upgrade-readiness
```

Use `make worker-recover APPLY=1` only after reviewing the dry-run output.
Use `make sdcpp-evidence RUN_SMOKE=1` only with an operator-configured video model.

## Interactive CLI control panel

```bash
sudo zmovie-ctl
```

The menu includes service health, production doctor, providers, projects, readiness, one-click production packaging, Bilibili session/job inspection, logs, backup, restart, upgrade and redacted configuration display.

Non-interactive examples:

```bash
sudo zmovie-ctl status
sudo zmovie-ctl health
sudo zmovie-ctl providers
sudo zmovie-ctl projects
sudo zmovie-ctl readiness prj_EXAMPLE
```

## Content + storyboard from CLI

```bash
sudo zmovie-ctl content \
  --topic "Launch zMovie for creator teams" \
  --brand ZeaZDev \
  --audience "video creators" \
  --goal "product launch and conversion" \
  --call-to-action "Create, render and publish with zMovie" \
  --duration 60
```

The result is persisted as a zMovie project with content beats, Character Bible, scenes, shots, production prompts, QC and director notes.

The Makefile shortcut is:

```bash
make content TOPIC='Launch zMovie for creator teams'
```

## Production operations

`mock` is rejected by the production path. Use a real configured provider such as `comfyui` or `webhook`.

```bash
make readiness PROJECT_ID=prj_EXAMPLE
make render PROJECT_ID=prj_EXAMPLE PROVIDER=comfyui
make assemble PROJECT_ID=prj_EXAMPLE
make prepare PROJECT_ID=prj_EXAMPLE
make export PROJECT_ID=prj_EXAMPLE
```

Or run the production package pipeline in one command:

```bash
make production PROJECT_ID=prj_EXAMPLE PROVIDER=comfyui
```

Equivalent CLI:

```bash
sudo zmovie-ctl production prj_EXAMPLE comfyui
```

The production command performs:

```text
render real media
  -> validate every shot
  -> strict FFmpeg assembly
  -> validate final media
  -> prepare Bilibili package
  -> export ZIP + checksums
  -> STOP at human approval gate
```

It does **not** approve or publish externally.

## Bilibili safety gates

Inspect the session and job:

```bash
sudo zmovie-ctl bili-session
sudo zmovie-ctl bili-status pub_EXAMPLE
```

Record explicit approval only after reviewing the exact package:

```bash
sudo zmovie-ctl bili-approve pub_EXAMPLE APPROVE
```

A real external submission requires a second explicit confirmation token:

```bash
sudo zmovie-ctl bili-publish pub_EXAMPLE CONFIRM-PUBLISH
```

That command performs a live session check and fail-closed publication preflight before one external submission attempt. A returned `submitted` state is **not** treated as public publication. Completion still requires a real public Bilibili URL and `remote_confirmation=true`.

## Docker and local development

```bash
make dev-setup
make dev

make compose-build
make compose-up
make compose-ps
make compose-logs
make compose-down
```

## Renderer installation

Install local ComfyUI with automatic backend detection:

```bash
make renderer-install
```

Force a backend when needed:

```bash
make renderer-install BACKEND=cpu
make renderer-install BACKEND=nvidia
make renderer-install BACKEND=rocm
```

Then configure the zMovie workflow:

```bash
make renderer-config
make doctor
```

A successful ComfyUI API smoke check does not by itself prove accelerated AI-video production. Production readiness requires a real configured video workflow and valid rendered media.
