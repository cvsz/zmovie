# zMovie Completion and Security Remediation Plan

> Execute this plan task-by-task, verifying each task before moving to the next.

**Goal:** close the repository-owned vulnerabilities and stale/incomplete work in zMovie, add regression and release gates, then create signed commits and push them to `origin/main` without rewriting existing history.

**Design:** `docs/superpowers/specs/2026-09-09-zmovie-completion-design.md`

**Validation environment:** `/tmp/zmovie-audit-venv-20260909` when present; otherwise create an isolated virtual environment outside the repository. Never add the environment, local configuration, database, media, or generated caches to Git.

## Task 1: Add regression coverage before implementation

**Files:** `tests/test_app.py`, `tests/test_platform.py`, `tests/test_media_preview.py`, add focused tests under `tests/` only where an existing module has no suitable fixture.

- Add tests that assert the default app has API docs disabled unless `ZMOVIE_ENABLE_DOCS=true`.
- Add tests for legacy admin protection, including unauthenticated and authenticated requests, while preserving direct function-call compatibility.
- Add tests for generation/login rate-limit rejection and `Retry-After` behavior.
- Add tests that public v2 health omits local paths and renderer configuration while retaining aggregate liveness fields.
- Add tests that asset registration rejects paths outside configured managed roots and symlink escapes.
- Add tests that an unset secret is not the historical source-controlled fallback.
- Run the focused tests and record the expected failures before changing production code.

## Task 2: Implement security boundaries and runtime defaults

**Files:** `app.py`, `main.py`, `zmovie_platform/auth.py`, `zmovie_platform/api_routes.py`, `zmovie_platform/health.py`, `zmovie_platform/publisher_routes.py`, `zmovie_platform/rate_limit.py`, `zmovie_platform/security.py`, `docker-compose.yml`, `.env.example`.

- Add the explicit docs-enable setting and protect legacy state/history routes through the existing bearer-token model.
- Redirect the legacy root to `/studio` so the default operator path does not bypass the authenticated UI.
- Make direct `python app.py` launch the composed `main:app` service instead of a legacy-only server.
- Add request-keyed throttling to login, bootstrap, and legacy generation with bounded `429` responses.
- Replace the known auth fallback with an ephemeral random key and document persistent-secret requirements.
- Add a sanitized public health projection and route v2 health through it.
- Validate asset paths against managed roots after resolving symlinks.
- Serialize publisher responses without server-local path fields.
- Keep internal/CLI diagnostic detail available where existing operational tooling requires it.
- Run focused tests and the complete existing suite; repair regressions at their source.

## Task 3: Upgrade dependencies and quality gates

**Files:** `requirements.txt`, `.github/workflows/test.yml`, add `ruff.toml` or an equivalent focused configuration, `install.sh`, `scripts/install-comfyui.sh`.

- Pin the patched FastAPI/Starlette versions already validated in the isolated environment.
- Add CI checks for dependency auditing, focused Ruff rules, ShellCheck, both frontend JavaScript entry points, and Compose configuration.
- Fix the two unsafe shell trap forms and any actionable focused lint findings without broad stylistic churn.
- Preserve the existing Python matrix and Docker/build/test gates.
- Run `pip check`, `pip-audit`, Ruff, ShellCheck, JavaScript syntax checks, and Compose validation locally.

## Task 4: Correct stale completion and deployment documentation

**Files:** `README.md`, `zmovie_platform/README_CI.md`, `zmovie_platform/README_API_ENTRY.md`, `zmovie_platform/README_API_READY.md`, `zmovie_platform/README_APP.md`, `zmovie_platform/README_DEPLOYMENT.md`, `zmovie_platform/README_DOCKER.md`, `zmovie_platform/README_LAST.md`, `zmovie_platform/README_NEXT.md`, `zmovie_platform/README_START.md`, and directly affected environment/install docs.

- Replace claims that the v2 API is still waiting for entry-point integration with the current `main:app` architecture.
- Correct production and Docker health paths and document the explicit docs flag.
- Update the CI Python-version statement to match the workflow.
- Consolidate remaining external integration gates as explicit, truthful acceptance requirements instead of marking them complete.
- Search again for `TODO`, `NEXT`, incomplete, placeholder, and stale entry-point claims; resolve repository-owned items or document genuine external blockers.

## Task 5: Verify, sign, and push

**Files:** only files changed by Tasks 1–4.

- Inspect `git diff`, `git diff --check`, status, and the staged file list for scope and secret hygiene.
- Configure the repository to use the preferred local GPG key and verify `gpg-agent` responsiveness.
- Create signed commits with `git commit -S`; verify each with `git verify-commit` and `git log --show-signature`.
- Confirm the remote main SHA before pushing, then push with `env -u GITHUB_TOKEN git push origin HEAD:refs/heads/main`.
- Re-query the remote SHA and monitor the resulting GitHub Actions runs. If a check fails, repair it in a new signed commit and re-run the gates.
- Report local verification, remote commit/signature state, CI state, runtime caveats, and the remaining external gates separately.
