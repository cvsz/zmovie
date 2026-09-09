# Docker deployment

See the [documentation index](../docs/INDEX.md) for canonical guides and
cross-component procedures.

Docker deployment runs the API as an unprivileged user, mounts persistent data, exposes the configured HTTP port, and performs health checks against `/api/v2/health`.
API documentation is disabled by default; set `ZMOVIE_ENABLE_DOCS=true` in the Compose environment only for controlled debugging.
