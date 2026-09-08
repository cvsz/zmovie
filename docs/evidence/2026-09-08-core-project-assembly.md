# Verified Runtime Evidence — core / Project Assembly

Date: 2026-09-08 UTC
Host: `core`
Scope: zMovie native systemd deployment → storyboard → QC → mock render jobs → FFmpeg assembly → final MP4 validation

## Result

PASS.

Verified from operator-provided runtime output:

- zMovie native installation completed healthy.
- The project smoke gate executed storyboard generation, QC, mock render jobs, and FFmpeg assembly.
- Final movie path: `/var/lib/zmovie/media/prj_e19df013c8e4/final.mp4`.
- `ffprobe` identified a valid H.264 video stream.
- Resolution: 1280×720.
- Display aspect ratio: 16:9.
- Pixel format: yuv420p.
- Frame rate: 24 fps.
- Duration: approximately 10.083 seconds.
- MP4 container probe score: 100.
- The smoke gate reported PASS.

## Readiness boundary

This proves the project-level orchestration, render-job persistence, FFmpeg assembly path, and final-video validation on the native `core` deployment.

It does **not** prove accelerated AI-video inference. The same runtime output reported ComfyUI `2.14.0+cpu`, device type `cpu`, `accelerated=false`, `render_ready=true`, and `production_video_ready=false`.

The local ComfyUI workflow in this evidence is a non-production connectivity workflow. A real production-video gate still requires an accelerated ComfyUI host and a role=`video` API workflow.

## Next evidence gates

1. Prepare a Bilibili publication package from the verified final movie without publishing it.
2. Configure a private accelerated ComfyUI host and production video workflow.
3. Run the production-video smoke gate and validate the resulting video with `ffprobe`.
4. Verify Bilibili authenticated browser session.
5. Perform a controlled Bilibili test submission.
