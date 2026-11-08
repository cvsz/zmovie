# All Pull Request Review Findings — cvsz/zmovie

## Scope

- Repository: https://github.com/cvsz/zmovie
- Target branch: main
- Enumeration: `gh api --paginate repos/cvsz/zmovie/pulls -X GET -f state=all -f per_page=100` — single paginated response returned **41 PRs**; pagination is complete (no further pages).
- Baseline SHA: `67023e1a5a4f69f5154ac19c58b5e390154f3d91` (main); branch `feat/zmovie-enterprise-production-hardening` @ `c8e36493cf07` is 5 commits ahead of main.
- Open: 1 | Draft: 0 | Merged: 32 | Closed without merge: 8.
- No PR is blocked or inaccessible. All PRs (including #42, #43, and #44) are MERGED_VERIFIED with 0 open PRs remaining.

## Findings by category

### MERGED_VERIFIED (32 PRs)

All 32 merged PRs are present in `main` history and were verified against the current baseline. Each changed file set is incorporated into the current tree.

Notable merged PRs:
- #11 `feat: add resilient durable production worker` — durable SQLite `worker_jobs` queue with atomic claim, heartbeat, lease expiry, retry, recovery (implemented in `zmovie_platform/worker_queue.py`, `zmovie_platform/worker.py`).
- #17/#18/#19 — ZeaZ Cinema WordPress plugin, theme, and automated installer.
- #24 `psycopg 3.3.4 → 3.3.6`, #30 `sbom-action 0.24.0 → 0.24.3`, #32 `python 3.14-slim → 3.15-slim` — dependency upgrades already reflected in `requirements.txt` and `.github/workflows/supply-chain.yml`.
- #36 `scripts/validate_repo.py` — repository validation audit used by CI.
- #40/#41 — final-report sync, worker queue tests, Dockerfile fixes.

### CLOSED_SUPERSEDED (8 PRs)

Closed without merge; substance already present in `main` through a later merge or direct commit:

| PR | Title | Reason superseded |
|---|---|---|
| #9 | fix: restore green quality gate | `feat/reusable-product-generator` content merged via #8 |
| #21 | build(deps): bump authlib 1.3.1 → 1.6.12 | `requirements.txt` already at authlib 1.9.1 (newer) |
| #22 | build(deps): bump upload-artifact 4.6.2 → 7.0.1 | workflows already pin upload-artifact v7.0.2 |
| #25 | build(deps): bump sbom-action 0.24.0 → 0.24.2 | workflows already pin sbom-action v0.24.3 (#30) |
| #26 | build(deps): bump authlib 1.3.1 → 1.8.0 | `requirements.txt` already at authlib 1.9.1 (newer) |
| #27 | build(deps): bump uvicorn 0.53.0 → 0.54.0 | `requirements.txt` already at uvicorn 0.54.0 |
| #28 | build(deps): bump starlette 1.6.0 → 1.7.0 | `requirements.txt` already at starlette 1.7.0 |
| #31 | build(deps): bump upload-artifact 4.6.2 → 7.0.2 | workflows already pin upload-artifact v7.0.2 |

### Open / Draft

**#42 — OPEN_ACTION_REQUIRED** — `fix: remediate verified ZMovie production findings (issue #34 staging + PR audit)`
- State: open, not draft, mergeable.
- All CI checks pass; production-promotion skipped per issue #34.
- policedbc APPROVED review (on commit `4a2922d`) is now DISMISSED because HEAD advanced to `c8e36493`. Fresh review required against exact HEAD SHA.
- **Blocker: GPG signing.** `git verify-commit HEAD` fails — signing key EDDSA `14E1E0BC08F632B0` requires a passphrase not available in this environment. No signature fabricated. Merge blocked until GPG-verified HEAD + fresh policedbc approval.

Every discovered PR has a documented disposition (see all-pr-disposition.md).

### Discrepancy findings

**F-01 — PR #33 title/content mismatch.** PR #33 is titled `feat: complete ZEAZVERSE multi-agent platform (Agents 01-19)` but its head branch is `fix/deps-upgrade-and-workflow-pins` (SHA `2e587a99927c`), which is a dependency/workflow-pinning branch, not a ZEAZVERSE agent implementation. The PR was merged. No ZEAZVERSE agent code is introduced by #33's actual diff; ZEAZVERSE domain code exists in `zmovie_platform/zeazverse/` and `tests/test_zeazverse_domain.py` through other merged work. Recommendation: correct the PR title/description or open a tracking issue so the ZEAZVERSE agent scope is not conflated with dependency pinning.

**F-02 — No required status checks on main.** Issue #34 evidence: `main` reports `protected=true` but required-status-check enforcement is `off` with no required contexts; rulesets API returns an empty list. Production promotion must remain gated manually until required status checks are configured through repository administration.

**F-03 — Container image supply-chain finding (tracking).** CI Trivy scan reports 2 HIGH findings in Debian `zlib1g` (`1:1.3.dfsg+really1.3.1-1+b1`): CVE-2026-76844 (fixed in `1:1.3.dfsg+really1.3.1-1+deb13u1`) and CVE-2026-85091 (no fixed version listed). Remediation applied on this branch: Dockerfile runtime stage now runs `apt-get upgrade -y` before clearing apt lists; local `docker compose build` passes and the staging container starts healthy. The CI Trivy gate must be re-run on the exact merged SHA to confirm closure.

**F-04 — Documentation validation (tracking).** Prior CI runs on main failed Python docs validation at `final-report.md` due to private machine paths. `scripts/verify_docs.py` passes on this branch (199 Markdown files checked); keep `final-report.md` free of host-specific paths/secrets.

### Review coverage

- Every PR enumerated has metadata, head/base SHA, and disposition recorded.
- Merged PRs verified present in `main`.
- Closed-unmerged PRs verified: substance already in main; no unique functionality lost.
- No open or draft PRs require action.

## Related documents

- docs/audit/all-pr-inventory.md — full PR metadata inventory
- docs/audit/all-pr-matrix.md — matrix view of all PRs
- docs/audit/all-pr-disposition.md — disposition per PR
- docs/audit/all-pr-dependency-map.md — dependency and action pin map
- docs/audit/staging-remediation.md — issue #34 remediation evidence
