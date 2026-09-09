# zMovie API guide

The composed `main:app` service exposes the authenticated v2 production API
and retains the legacy prompt API for compatibility. API documentation is
disabled by default; enable it only in a controlled environment with
`ZMOVIE_ENABLE_DOCS=true`.

## Base routes

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/v2/health` | Public aggregate liveness projection. |
| `GET` | `/api/v2/capabilities` | Capability and provider catalog. |
| `POST` | `/api/v2/auth/login` | Authenticate an operator. |
| `GET` | `/api/v2/projects` | List projects visible to the authenticated principal. |
| `POST` | `/api/v2/projects` | Create a project. |
| `GET` | `/api/v2/projects/{id}/assets` | List managed project assets. |
| `GET` | `/api/v2/projects/{id}/qc` | Read project QC state. |
| `POST` | `/api/v2/projects/{id}/render` | Start a provider-backed render request. |
| `POST` | `/api/v2/projects/{id}/assemble` | Assemble validated shot media. |
| `POST` | `/api/v2/projects/{id}/export` | Create a validated production export. |
| `POST` | `/api/v2/pipeline` | Run the guarded project pipeline. |
| `GET` | `/api/v2/publish/bilibili/session` | Inspect scoped browser-session readiness. |
| `POST` | `/api/v2/projects/{id}/publish/bilibili/prepare` | Build a publication package. |
| `POST` | `/api/v2/publish/jobs/{id}/approve` | Approve the exact package. |
| `POST` | `/api/v2/publish/jobs/{id}/publish` | Attempt one externally submitted upload. |
| `GET` | `/api/v2/publish/jobs/{id}` | Read a publication job. |

The detailed module map is maintained in
[zmovie_platform/README_API_V2.md](../zmovie_platform/README_API_V2.md). Keep
this table aligned with the actual route registration when endpoints change.

## Authentication

When authentication is enabled, mutation, project, asset, render, export,
publisher, and legacy history/generation routes require an administrator or
authorized bearer token as defined by the route. Health and login/bootstrap
discovery are intentionally handled separately. Never put a token in a URL or
commit it in an example.

Example with a redacted token:

```bash
curl -fsS \
  -H 'Authorization: Bearer <REDACTED_TOKEN>' \
  http://127.0.0.1:8080/api/v2/projects
```

## Health and response safety

`/api/v2/health` returns aggregate service/version/readiness information suitable
for a public probe. Detailed filesystem paths, renderer configuration, and
diagnostic data belong to internal operator diagnostics. Public API serializers
must not expose server-local paths, credentials, or browser-state locations.

## Project and media contract

Project identifiers are server-generated `prj_*` values. Asset and render
operations are scoped to the project and must pass ownership checks. Media
previews are issued through the managed asset route and use short-lived signed
URLs; callers must not construct arbitrary filesystem paths.

Production rendering is accepted only when every shot has valid managed video
media. The mock provider is for dry runs and tests and is rejected by strict
production routes.

## Publication contract

The safe sequence is:

```text
prepare -> review exact package -> approve -> preflight -> submit -> confirm public URL
```

Submission may return `submitted` without a public URL. Completion requires a
valid public Bilibili URL and durable `remote_confirmation=true`. See the
[Bilibili runbook](BILIBILI_REAL_PUBLISH_RUNBOOK.md).

## Compatibility API

The legacy prompt endpoints and standalone `zmovie.py` generator remain
available for existing users. Their behavior is documented in the focused
[legacy API notes](../zmovie_platform/README_API_ENTRY.md),
[authentication notes](../zmovie_platform/README_API_AUTH.md), and
[history notes](../zmovie_platform/README_HISTORY.md). New integrations should
prefer v2 and should not infer production readiness from legacy prompt output.
