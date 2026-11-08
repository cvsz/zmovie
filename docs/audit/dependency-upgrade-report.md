# Dependency Upgrade Report — cvsz/zmovie

## Approach

Upgrades reviewed in small groups: Python requirements, GitHub Actions pins, Docker base image. Each change reviewed against release notes/advisories, runtime compatibility, and dependency constraints; reproducibility preserved. Nothing was blindly upgraded; nothing was downgraded to hide an error; integrity checks were not disabled.

## Python requirements (requirements.txt)

| Package | Version | pip-audit | Notes |
|---|---|---|---|
| authlib | 1.9.1 | clean | Newer than closed dependabot asks (#21 1.6.12, #26 1.8.0) |
| cryptography | 50.0.1 | clean | — |
| fastapi | 0.141.1 | clean | — |
| httpx | 0.28.1 | clean | — |
| psycopg | 3.3.6 | clean | #24 merged |
| python-multipart | 0.0.32 | clean | — |
| starlette | 1.7.0 | clean | #28 closed, superseded |
| uvicorn[standard] | 0.54.0 | clean | #27 closed, superseded |
| playwright | >=1.63.0,<2 | clean | #3, #15 |
| edge-tts | 7.2.8 | clean | — |

`.venv/bin/pip-audit -r requirements.txt` → "No known vulnerabilities found" (exit 0).

## GitHub Actions pins

All requested dependabot upgrades already present in main:
- actions/checkout v7 (#4, #23 merged)
- actions/setup-python v7 (#5 merged)
- actions/upload-artifact v7.0.2 (#31 closed — satisfied by current pin)
- docker/build-push-action v7.4.0 (#29 merged)
- anchore/sbom-action v0.24.3 (#30 merged; #25 closed — superseded)

## Docker base image

`FROM python:3.15-slim` (#32 merged). `docker compose build` passes.

## Supply-chain hardening applied on this branch

Dockerfile runtime stage now runs `apt-get upgrade -y` before clearing apt lists, so fixable OS vulnerabilities (e.g. Debian `zlib1g` CVE-2026-76844 / CVE-2026-85091 reported by CI Trivy on `python:3.15-slim`) receive available patches at image build time. Local `docker compose build` exit 0; staging container starts healthy.

## Tests after dependency changes

- unittest: 240 pass
- ruff check: pass
- compileall: pass
- pip-audit: clean

## Status

No pending dependency upgrades. All dependency work verified compatible with the Python 3.11–3.14 CI matrix (Dockerfile uses 3.15-slim for the container; local validation on 3.14.4).
