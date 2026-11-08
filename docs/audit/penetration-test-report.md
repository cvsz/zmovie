# Penetration Test Report — cvsz/zmovie

## Scope

Authorized local/staging environment only (this repository checkout and the locally run Docker Compose stack on host port 19080). Synthetic data only. No destructive tests. No unrelated hosts. No data exfiltration. No production testing.

## Method

- Static source review of authentication, authorization, RBAC, CSRF, XSS, SSRF, SQL injection, command injection, path traversal, file upload, deserialization, webhook signature, secret handling, rate limits, container security, network exposure.
- Review of `.env`, `.env.example`, `.git-credentials` tracking status.
- Review of Docker Compose security options (`no-new-privileges`, `cap_drop: ALL`, tmpfs, `shm_size`, non-root user).
- Review of workflow permissions and CI artifacts.
- Local health/readyz endpoint validation against the running container.

## Findings

None verified as exploitable in this environment.

### Security boundaries confirmed (by design and tests)

- Authentication enabled by default (`ZMOVIE_AUTH_ENABLED=true`).
- Admin bootstrap requires loopback + `ZMOVIE_ADMIN_PASSWORD` (>= 10 chars).
- `validate_runtime_settings()` rejects non-loopback bind without auth and a >=32-char `ZMOVIE_SECRET_KEY`.
- Project ownership checks on mutation/project/asset/render/export/publisher routes.
- Rate limiting on legacy generate (30/60s), auth bootstrap (5/60s), auth login (10/60s).
- Queue payloads reject credential-like fields.
- Media preview URLs signed, short-lived, scoped to managed MP4 assets; arbitrary filesystem paths rejected (`validate_managed_asset_path`).
- Asset path registration rejects symlink escapes.
- Bilibili auto-publish disabled by default; explicit exact-package approval + `CONFIRM-PUBLISH` required; `submitted` is not retried blindly (`recovery_required`/`external_state_unknown`).
- ComfyUI/webhook provider URLs restricted to http(s); tokens not logged.
- Container: `no-new-privileges:true`, `cap_drop: ALL`, `USER zmovie` (uid 10001), tmpfs `/tmp`, `shm_size: 1gb`, `host.docker.internal` gateway mapping only.
- `.env` and `.git-credentials` are gitignored — not tracked; no credential values in repository history.
- `pip-audit -r requirements.txt` — no known vulnerabilities.
- Secret scan workflow (`secret-scan.yml`) present; no active secrets found in tracked files.

### Not performed (require external authorization/credentials)

- Live OAuth/token exchange with YouTube or Bilibili (no credentials; would require explicit approval).
- Real Bilibili Creator Center publication (fail-closed; explicit human approval required).
- External network-based active scanning beyond localhost.

## Status

No Critical or High security findings unresolved. Penetration scope limited to authorized local/staging synthetic tests; all passed. No production traffic or DNS cutover was performed.
