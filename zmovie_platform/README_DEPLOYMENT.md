# Deployment entry points

See the [documentation index](../docs/INDEX.md) for canonical guides and
cross-component procedures.

Deployment entry points: native `install.sh`, Docker Compose, or direct `uvicorn main:app`. The installer configures persistent data and environment state.
API documentation is disabled by default; set `ZMOVIE_ENABLE_DOCS=true` only in a controlled environment when `/docs` is needed.
