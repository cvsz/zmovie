# zMovie documentation index

This index is the navigation source for the zMovie documentation set. Start
with the path that matches your role, then use the focused guides for a
provider or publication workflow.

## Start here by audience

| Audience | First read | Then use |
| --- | --- | --- |
| New user | [README](../README.md) | [FAQ](FAQ.md), [local development](../README.md#local-development) |
| Native operator | [Operations](OPERATIONS.md) | [Long-running worker](LONG_RUNNING_RENDER_WORKER.md), [Backup and recovery](BACKUP_AND_RECOVERY.md) |
| Docker operator | [Docker guide](../zmovie_platform/README_DOCKER.md) | [Operations](OPERATIONS.md), [Configuration](CONFIGURATION.md) |
| API client | [API guide](API.md) | [API v2 module map](../zmovie_platform/README_API_V2.md), [authentication](../zmovie_platform/README_API_AUTH.md) |
| Renderer operator | [Architecture](ARCHITECTURE.md) | [Vulkan renderer](VULKAN_RENDERER.md), [ComfyUI remote GPU](COMFYUI_REMOTE_GPU.md), [stable-diffusion.cpp](SDCPP_LOCAL_RENDERER.md) |
| Bilibili operator | [Bilibili runbook](BILIBILI_REAL_PUBLISH_RUNBOOK.md) | [publication model](BILIBILI_PUBLISHING.md), [completion gate](BILIBILI_PRODUCTION_COMPLETION.md) |
| Developer | [Architecture](ARCHITECTURE.md) | [Testing](TESTING.md), [API](API.md), module READMEs |
| Contributor | [CONTRIBUTING](../CONTRIBUTING.md) | [Documentation standard](DOCUMENTATION_STANDARD.md), [i18n](I18N.md) |
| Maintainer | [Release](RELEASE.md) | [Status](STATUS.md), [Runtime evidence](RUNTIME_EVIDENCE.md), [Security](../SECURITY.md), [Changelog](../CHANGELOG.md) |

## Canonical project guides

- [Architecture](ARCHITECTURE.md)
- [API](API.md)
- [Configuration](CONFIGURATION.md)
- [Operations](OPERATIONS.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Testing](TESTING.md)
- [Release](RELEASE.md)
- [Status](STATUS.md)
- [I18N](I18N.md)
- [Documentation standard](DOCUMENTATION_STANDARD.md)
- [FAQ](FAQ.md)

## Focused workflow guides

- [Long-running render worker](LONG_RUNNING_RENDER_WORKER.md)
- [Vulkan renderer isolation](VULKAN_RENDERER.md)
- [Backup and recovery](BACKUP_AND_RECOVERY.md)
- [Runtime evidence](RUNTIME_EVIDENCE.md)
- [Makefile and CLI control](MAKEFILE_CLI_CONTROL.md)
- [ComfyUI remote GPU](COMFYUI_REMOTE_GPU.md)
- [ComfyUI workflow integration](../workflows/comfyui/README.md)
- [stable-diffusion.cpp local renderer](SDCPP_LOCAL_RENDERER.md)
- [Hyperframes](HYPERFRAMES.md)
- [Bilibili publishing](BILIBILI_PUBLISHING.md)
- [Bilibili production completion](BILIBILI_PRODUCTION_COMPLETION.md)
- [Bilibili real-publication runbook](BILIBILI_REAL_PUBLISH_RUNBOOK.md)
- [GitHub environment clone](GITHUB_ENVIRONMENT_CLONE.md)
- [YouTube roadmap](YOUTUBE_ROADMAP.md)
- [Wan prompt generator](../prompts/WAN3_MASTER_ACTION_GENERATOR.md)

## Evidence and internal reference

- [ComfyUI smoke evidence](evidence/2026-09-08-core-comfyui-smoke.md)
- [Project assembly evidence](evidence/2026-09-08-core-project-assembly.md)
- [Bilibili live-session evidence](evidence/2026-09-09-core-bilibili-live-session.md)
- [Bilibili scope/auth evidence](evidence/2026-09-09-core-bilibili-scope-auth-verified.md)
- [Cloudflare public-ingress evidence](evidence/2026-09-09-cloudflare-public-ingress.md)
- [Platform module map](../zmovie_platform/README_API.md)
- [Platform internals](../zmovie_platform/README_INTERNAL.md)

Evidence records what was observed at a point in time. It does not replace a
fresh runtime probe, hosted CI result, external publication confirmation, or
current source inspection.

## Maintenance rules

When a command, API contract, status claim, or user-facing message changes,
update the relevant canonical guide and its focused deep link. Follow the
[documentation standard](DOCUMENTATION_STANDARD.md) and the
[i18n standard](I18N.md).
