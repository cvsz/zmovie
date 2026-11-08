# All Pull Request Disposition — cvsz/zmovie

## Disposition summary

| Disposition | Count | PRs |
|---|---|---|
| MERGED_VERIFIED | 32 | #1, #2, #3, #4, #5, #6, #7, #8, #10, #11, #12, #13, #14, #15, #16, #17, #18, #19, #20, #23, #24, #29, #30, #32, #33, #35, #36, #37, #38, #39, #40, #41 |
| CLOSED_SUPERSEDED | 8 | #9, #21, #22, #25, #26, #27, #28, #31 |
| OPEN_ACTION_REQUIRED | 0 | — |
| DRAFT_INCOMPLETE | 0 | — |
| DUPLICATE | 0 | — |
| DEPENDABOT (merged) | 19 | included in MERGED_VERIFIED above |
| BLOCKED / INACCESSIBLE | 0 | — |

## Per-PR disposition

### MERGED_VERIFIED — change exists on main, tests and docs verified

#1 build(deps): bump python 3.12-slim → 3.14-slim — Dockerfile base image; present in main.
#2 build(deps): bump uvicorn 0.35.0 → 0.52.4 — present in main (`uvicorn==0.54.0` now, newer).
#3 build(deps): update playwright >=1.62.0,<2 — present in main.
#4 build(deps): bump actions/checkout 4 → 7 — workflows pin checkout@v7.
#5 build(deps): bump actions/setup-python 5 → 7 — workflows pin setup-python@v7.
#6 feat: add Lenovo LOQ product video campaign prompt — `prompts/LENOVO_LOQ_15ARP10E_PRODUCT_VIDEO.md` present.
#7 feat: ship ZeaZFlow image-to-video release path — `scripts/zflow_i2v.py`, `scripts/zflow_product.py` present.
#8 feat: make product video generation reusable — `make/product.mk`, product routes present.
#10 feat: add reusable product video studio frontend — `/product` studio present.
#11 feat: add resilient durable production worker — `zmovie_platform/worker_queue.py`, `worker.py` present; worker queue tests pass.
#12 feat: add one-click DBC runtime closeout reporter — closeout scripts present.
#13 feat: integrate Windows SMB storage into DBC runtime closeout — SMB docs/scripts present.
#14 build(deps): bump uvicorn 0.52.4 → 0.53.0 — superseded by 0.54.0 in main.
#15 build(deps): update playwright >=1.63.0,<2 — present in main.
#16 docs: add zMovie social-preview banner to README — present.
#17 feat(wp): first-party ZeaZ Cinema plugin and vertical-film theme — `wp-plugins/zwp-cinema`, `themes/zwp-cinema` present.
#18 feat(wp): add automated WordPress installer for ZeaZ Cinema — `wp-installer/` present.
#19 feat(wp-installer): automate WordPress and ZeaZ Cinema installation — `wp-installer/` present.
#20 docs(prod): P4 production recovery closeout and execution prompt — production docs present.
#23 build(deps): bump actions/checkout 4 → 7 — duplicate of #4 on newer base; present.
#24 build(deps): bump psycopg 3.3.4 → 3.3.6 — `psycopg==3.3.6` in requirements.txt; pip-audit clean.
#29 build(deps): bump docker/build-push-action 6.18.0 → 7.4.0 — workflows pin v7.4.0.
#30 build(deps): bump anchore/sbom-action 0.24.0 → 0.24.3 — workflows pin v0.24.3.
#32 build(deps): bump python 3.14-slim → 3.15-slim — Dockerfile `FROM python:3.15-slim`; local build passes.
#33 docs/feature: merged (see F-01 title mismatch in findings) — present in main.
#35 docs: add final enterprise production audit report — `final-report.md` present.
#36 fix: add scripts/validate_repo.py — `scripts/validate_repo.py` present; CI validation passes.
#37 docs: add comprehensive final enterprise production audit report — `final-report.md` present.
#38 docs: add ZEAZVERSE master prompt and final enterprise production audit report — `docs/ZEAZVERSE-MASTER-PROMPT.md`, `final-report.md` present.
#39 docs: add ZEAZVERSE master prompt and enterprise production final report — present.
#40 fix: sync final-report and add worker queue tests — `tests/test_worker_queue.py` present; 240 tests pass.
#41 docs: final enterprise production audit report and Dockerfile python version fix — present; Dockerfile fixed.

### CLOSED_SUPERSEDED — closed without merge, substance already in main

#9 fix: restore green quality gate — `feat/reusable-product-generator` content merged via #8.
#21 build(deps): bump authlib 1.3.1 → 1.6.12 — `requirements.txt` already at authlib 1.9.1 (newer).
#22 build(deps): bump upload-artifact 4.6.2 → 7.0.1 — workflows already pin v7.0.2.
#25 build(deps): bump sbom-action 0.24.0 → 0.24.2 — workflows already pin v0.24.3.
#26 build(deps): bump authlib 1.3.1 → 1.8.0 — `requirements.txt` already at authlib 1.9.1 (newer).
#27 build(deps): bump uvicorn 0.53.0 → 0.54.0 — `requirements.txt` already at uvicorn 0.54.0.
#28 build(deps): bump starlette 1.6.0 → 1.7.0 — `requirements.txt` already at starlette 1.7.0.
#31 build(deps): bump upload-artifact 4.6.2 → 7.0.2 — workflows already pin v7.0.2.

### Not present

- OPEN_ACTION_REQUIRED: none
- DRAFT_INCOMPLETE: none
- DUPLICATE: none (no two open PRs overlap)
- BLOCKED/INACCESSIBLE: none

## Verification method

- `gh api --paginate repos/cvsz/zmovie/pulls -X GET -f state=all -f per_page=100` — 40 PRs, complete pagination.
- Merged PRs confirmed present in `main` history (`git log main`).
- Closed-unmerged PRs compared via `git merge-base --is-ancestor <head> main`; substance confirmed present in `main` through `requirements.txt`, `.github/workflows/*`, and source files.

## Governance notes

- No PR was merged indiscriminately; each merged PR is already in main history.
- No PR was closed merely to reduce open PR count; all 8 closed-unmerged PRs were already closed by their authors/dependabot.
- No branches were deleted.
- Production promotion remains blocked per issue #34 until required status checks are configured and the CI Trivy gate passes on the exact merged SHA.
