# Remote GPU ComfyUI Runbook

zMovie can remain on the control-plane host while ComfyUI runs on a separate accelerated renderer. This is the recommended production topology when the zMovie host is CPU-only.

## Readiness model

zMovie intentionally distinguishes two states:

- `render_ready=true`: FFmpeg/FFprobe are present and the configured ComfyUI workflow is reachable, valid, and has no missing node types.
- `production_video_ready=true`: all of the above **plus** the workflow is explicitly classified as `video` and ComfyUI reports at least one non-CPU accelerator device.

A model-free smoke workflow can therefore prove the API integration without incorrectly claiming production AI-video readiness.

## Network boundary

Do not expose an unauthenticated ComfyUI API directly to the public internet.

Preferred connectivity:

1. private LAN/VLAN;
2. WireGuard/Tailscale/private overlay;
3. SSH/VPN tunnel;
4. HTTPS reverse proxy with authentication when a private network is not available.

The helper refuses plain HTTP to a public or unclassifiable host by default. `ZMOVIE_ALLOW_INSECURE_REMOTE_COMFYUI=true` exists only as an explicit operator override.

## Configure a production renderer

On the GPU machine, ComfyUI must answer:

```bash
curl -fsS http://GPU-PRIVATE-IP:8188/system_stats | python3 -m json.tool
```

Confirm that `devices` contains a non-CPU device.

Export the production video workflow from ComfyUI in API format and place that JSON on the zMovie host. Then run:

```bash
sudo bash /opt/zmovie/scripts/configure-remote-comfyui.sh \
  /path/to/video_workflow_api.json \
  http://GPU-PRIVATE-IP:8188
```

The helper:

- validates URL/network safety;
- probes `/system_stats`;
- refuses a renderer with CPU-only devices;
- installs the workflow on the zMovie host;
- marks the workflow role as `video`;
- restarts zMovie;
- validates required node types through `/object_info`;
- requires `production_video_ready=true` before returning success.

## Verify a real video render

After remote configuration passes:

```bash
sudo bash /opt/zmovie/scripts/smoke-production-video.sh
```

This submits a five-second shot through the native zMovie ComfyUI provider, downloads the output, requires `kind=video`, and validates the result with `ffprobe` before returning PASS.

The output is persisted under:

```text
/var/lib/zmovie/media/comfyui-production-smoke/
```

Only after this gate passes should the renderer be counted as real video-render evidence.

## Restore local smoke renderer

To switch back to the local model-free integration workflow:

```bash
sudo bash /opt/zmovie/scripts/smoke-zmovie-comfyui.sh
```

That sets the workflow role to `smoke`, so `render_ready` may be true while `production_video_ready` remains false.

## Evidence gates

A production AI-video renderer should have all of these confirmed:

```text
ComfyUI reachable             ✅
Workflow API JSON valid       ✅
Required nodes installed      ✅
Accelerator detected          ✅
Workflow role = video         ✅
production_video_ready        ✅
Real short-shot render        ✅
Downloaded video exists       ✅
ffprobe video validation      ✅
```

Project-level FFmpeg assembly and controlled Bilibili publishing are separate evidence gates after renderer verification.
