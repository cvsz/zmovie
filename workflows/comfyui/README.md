# ComfyUI workflow integration

zMovie can render shots through a self-hosted ComfyUI server using ComfyUI's API workflow JSON.

## 1. Build and verify the workflow in ComfyUI

Create a working text-to-video or image-to-video workflow in ComfyUI and verify that it produces a downloadable output (MP4/WebM/MOV/GIF/WebP or an image).

## 2. Export in API format

Export/save the workflow in **API format**, not the normal UI graph format. The resulting JSON should be an object keyed by node IDs, with each node containing `class_type` and `inputs`.

Save it as:

```text
workflows/comfyui/workflow_api.json
```

This file is intentionally not committed because model/custom-node graphs vary by installation.

## 3. Add zMovie placeholders

You may put these placeholders anywhere in string values inside the API workflow. zMovie recursively replaces them before queueing the workflow:

| Placeholder | Value |
|---|---|
| `{{PROMPT}}` | zMovie shot prompt |
| `{{NEGATIVE_PROMPT}}` | shot negative prompt |
| `{{SEED}}` | deterministic or configured seed |
| `{{WIDTH}}` | width derived from aspect ratio |
| `{{HEIGHT}}` | height derived from aspect ratio |
| `{{FRAMES}}` | frame count derived from duration/FPS |
| `{{FPS}}` | configured FPS |
| `{{DURATION_SECONDS}}` | shot duration |
| `{{ASPECT_RATIO}}` | project aspect ratio |
| `{{PREFIX}}` | unique output filename prefix |
| `{{JOB_ID}}` | zMovie render job ID |
| `{{PROJECT_ID}}` | zMovie project ID |
| `{{SHOT_ID}}` | zMovie shot ID |

Example fragment:

```json
{
  "6": {
    "class_type": "CLIPTextEncode",
    "inputs": {"text": "{{PROMPT}}", "clip": ["4", 1]},
    "_meta": {"title": "Positive Prompt"}
  },
  "7": {
    "class_type": "CLIPTextEncode",
    "inputs": {"text": "{{NEGATIVE_PROMPT}}", "clip": ["4", 1]},
    "_meta": {"title": "Negative Prompt"}
  }
}
```

The fragment above is illustrative only; use your own complete working video workflow.

## 4. Node-ID injection alternative

If editing placeholders is inconvenient, configure comma-separated node IDs:

```bash
ZMOVIE_COMFYUI_POSITIVE_NODE_IDS=6
ZMOVIE_COMFYUI_NEGATIVE_NODE_IDS=7
ZMOVIE_COMFYUI_SEED_NODE_IDS=25
ZMOVIE_COMFYUI_FRAMES_NODE_IDS=40
ZMOVIE_COMFYUI_SIZE_NODE_IDS=38
```

For prompt nodes, zMovie also detects nodes whose `_meta.title` contains `Positive` or `Negative` and have a `text` input.

## 5. Runtime configuration

Native install, when ComfyUI runs on the same host:

```bash
ZMOVIE_COMFYUI_URL=http://127.0.0.1:8188
ZMOVIE_COMFYUI_WORKFLOW=/opt/zmovie/workflows/comfyui/workflow_api.json
```

Docker zMovie with ComfyUI running on the Docker host:

```bash
ZMOVIE_COMFYUI_URL=http://host.docker.internal:8188
ZMOVIE_COMFYUI_WORKFLOW=/app/workflows/comfyui/workflow_api.json
```

The compose file mounts `./workflows/comfyui` read-only into the zMovie container and maps `host.docker.internal` to the Docker host on Linux.

## Wan-family timing

The defaults are optimized for a common Wan-style frame constraint:

```bash
ZMOVIE_COMFYUI_FPS=16
ZMOVIE_COMFYUI_FRAME_MULTIPLE=4
ZMOVIE_COMFYUI_FRAME_OFFSET=1
```

This shapes the generated frame count to `4n+1` (for example, a nominal 5 seconds at 16 FPS resolves to 81 frames). Change these values to match the workflow/model you actually use.

## Output handling

zMovie queues the workflow through `/prompt`, polls `/history/{prompt_id}`, discovers output-file records recursively, downloads them through `/view`, and stores the files under the project render directory. The first video-like output is selected as the primary render asset.

## Security

Keep ComfyUI bound to localhost/private networking where possible. Do not expose an unauthenticated ComfyUI server directly to the public internet. If a reverse proxy adds authentication, configure `ZMOVIE_COMFYUI_TOKEN` or `ZMOVIE_COMFYUI_HEADERS_JSON` for zMovie's server-to-server requests.
