# Runtime evidence

zMovie treats implementation, CI and real renderer execution as different evidence states.

`zmovie-ctl sdcpp-evidence` records an inspection report under the configured evidence directory (native default `/var/lib/zmovie/evidence`). The report contains host/runtime facts such as `/dev/dri` render-node visibility, Vulkan tooling, `sd-cli --list-devices`, FFmpeg/FFprobe availability and model-root presence. It does not claim a real model succeeded.

```bash
sudo zmovie-ctl sdcpp-evidence
```

A real model smoke is an explicit action and must use a configured video-capable model. No model weights are downloaded automatically.

```bash
sudo zmovie-ctl sdcpp-evidence --run-smoke
```

The current evidence command fails closed when it cannot safely infer a model-specific smoke invocation. In that case the evidence remains `real_model_verified=false`; configure the maintained stable-diffusion.cpp video bundle and run its real renderer smoke separately, then validate the result with FFprobe and record its SHA256.

A valid real-model artifact must contain a real video stream, positive duration and dimensions, and non-zero file size. A generated black test clip, metadata JSON, mock provider output or image renamed as video is not AI runtime evidence.

Recommended production evidence collection also records the exact repository SHA, hostname, OS/kernel, selected backend, model configuration/readability, output media facts and SHA256. Runtime evidence must come from the actual production host, not GitHub Actions.
