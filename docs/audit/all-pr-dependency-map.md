# All Pull Request Dependency Map — cvsz/zmovie

## Python dependencies (requirements.txt)

| Package | Pinned version | Related PR | Status |
|---|---|---|---|
| authlib | 1.9.1 | #21 (1.6.12 closed, superseded), #26 (1.8.0 closed, superseded) | Current; newer than all closed dependabot asks |
| cryptography | 50.0.1 | — | Current |
| fastapi | 0.141.1 | — | Current |
| httpx | 0.28.1 | — | Current |
| psycopg | 3.3.6 | #24 (merged) | Current |
| python-multipart | 0.0.32 | — | Current |
| starlette | 1.7.0 | #28 (closed, superseded) | Current |
| uvicorn[standard] | 0.54.0 | #2 (0.52.4), #14 (0.53.0), #27 (0.54.0 closed, superseded) | Current |
| playwright | >=1.63.0,<2 | #3 (>=1.62.0), #15 (>=1.63.0) | Current |
| edge-tts | 7.2.8 | — | Current |

Dependency audit: `.venv/bin/pip-audit -r requirements.txt` → "No known vulnerabilities found" (exit 0).

## GitHub Actions pins (.github/workflows/*)

| Action | Pinned ref | Related PR | Status |
|---|---|---|---|
| actions/checkout | v7 (`3d3c42e5...`) | #4, #23 (merged) | Current |
| actions/setup-python | v7 (`e555e519...`) | #5 (merged) | Current |
| actions/upload-artifact | v7.0.2 (`cf430e03...`) | #22 (7.0.1 closed), #31 (7.0.2 closed) | Current — satisfies #31's ask |
| docker/build-push-action | v7.4.0 (`c3c9e263...`) | #29 (merged) | Current |
| anchore/sbom-action | v0.24.3 (`66cbf4bc...`) | #25 (0.24.2 closed), #30 (0.24.3 merged) | Current |

## Docker base image

| Image | Tag | Related PR | Status |
|---|---|---|---|
| python | 3.15-slim | #1 (3.12→3.14), #32 (3.14→3.15, merged) | Current; `docker compose build` passes |

## Dependency changes pending

None. All dependabot PRs are either merged or superseded by a newer pinned version already in main. No open dependabot PRs remain.

## Notes

- Closed dependabot PRs (#21, #22, #25, #26, #27, #28, #31) were closed without merge, but every requested version is already present in main via a later merge or direct commit, so no dependency work is lost.
- `pip-audit` reports no known vulnerabilities for the pinned Python requirements.
- Supply-chain CI (`supply-chain.yml`) builds the container, generates a CycloneDX SBOM, runs a blocking Trivy HIGH/CRITICAL scan, and gates staging/production promotion behind it.
