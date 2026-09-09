# zMovie Documentation and GitHub Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the missing project and GitHub documentation, define a truthful multilingual i18n standard, and bring every existing Markdown file into a consistent navigable documentation system.

**Architecture:** Keep `README.md` as the short entry point and make `docs/INDEX.md` the canonical audience map. Add focused guides for architecture, API, configuration, operations, testing, release, status, troubleshooting, FAQ, documentation rules, and i18n while preserving specialized guides and evidence files. Add a dependency-free verifier that checks required files, safe relative links, headings, locale contracts, and secret/path hygiene in the documentation surface.

**Tech Stack:** Markdown, GitHub community files and issue forms, GitHub Actions YAML, Python 3 standard library, the existing `unittest` suite, and the existing `make`/Docker quality gates.

## Global Constraints

- Use the MIT License with `Copyright (c) 2026 cvsz`.
- Keep technical documentation, code comments, keys, and configuration names in English; localized examples may include Thai content.
- Use `en-US` as the default locale and `th-TH` as the first additional locale in the i18n standard.
- The current UI has no runtime locale catalog or localization layer; documentation must not claim that localization is implemented.
- Preserve the distinction between implemented behavior, verified runtime evidence, pending external acceptance, and deferred roadmap work.
- Never add credentials, browser state, tokens, environment values, or private machine paths to documentation, templates, examples, or commits.
- Preserve evidence files and historical design/plan meaning; do not rewrite history or turn external caveats into completion claims.
- Preserve the unrelated untracked `.env.mikrotik.stage`; stage only files belonging to this plan.
- Use the configured GPG key `220A4C8CCC7D2D50` for new commits and never force-update existing history.
- Run documentation checks from the repository root. Use an isolated dependency environment for the full project suite because the current system interpreter lacks `edge_tts`.

## File Map

### New root and GitHub files

- `LICENSE` — complete MIT license text.
- `CONTRIBUTING.md` — development, testing, documentation, i18n, security, and signed-commit contribution rules.
- `CODE_OF_CONDUCT.md` — Contributor Covenant with private reporting guidance.
- `SECURITY.md` — vulnerability reporting, supported versions, and credential/browser-state safety.
- `SUPPORT.md` — routing for support, bugs, features, and security reports.
- `CHANGELOG.md` — evidence-backed Unreleased history and release-entry rules.
- `.github/CODEOWNERS` — default ownership by `@cvsz`.
- `.github/pull_request_template.md` — review checklist for code, docs, i18n, tests, secrets, and evidence.
- `.github/ISSUE_TEMPLATE/bug_report.yml` — structured reproducible bug intake.
- `.github/ISSUE_TEMPLATE/feature_request.yml` — scoped feature proposal intake.
- `.github/ISSUE_TEMPLATE/config.yml` — issue routing and security/support links.
- `.github/dependabot.yml` — weekly dependency updates for pip, Docker, and GitHub Actions.

### New canonical project guides

- `docs/INDEX.md` — audience-based documentation map.
- `docs/ARCHITECTURE.md` — service, storage, provider, pipeline, and deployment boundaries.
- `docs/API.md` — v2 and compatibility API contracts without local-path leakage.
- `docs/CONFIGURATION.md` — environment variables, defaults, precedence, and secret handling.
- `docs/OPERATIONS.md` — install, upgrade, health, backup, restore, logs, readiness, and publication safety.
- `docs/TROUBLESHOOTING.md` — evidence-first diagnosis and recovery paths.
- `docs/TESTING.md` — local/CI checks, isolated dependencies, and known environment prerequisites.
- `docs/RELEASE.md` — signed commit, verification, push, hosted CI, and external evidence requirements.
- `docs/STATUS.md` — common status vocabulary and current project boundaries.
- `docs/I18N.md` — BCP 47, catalogs, fallback, formatting, accessibility, API, and translation QA standard.
- `docs/DOCUMENTATION_STANDARD.md` — Markdown, examples, links, evidence, terminology, and security rules.
- `docs/FAQ.md` — concise user/operator answers and the mock-provider boundary.

### Verification files

- `scripts/verify_docs.py` — dependency-free documentation contract verifier.
- `tests/test_docs_verifier.py` — focused tests for verifier behavior.
- `.github/workflows/test.yml` — invoke the documentation verifier while retaining all current jobs and gates.

## Task 1: Build the documentation contract verifier

**Files:**
- Create: `scripts/verify_docs.py`
- Create: `tests/test_docs_verifier.py`

**Interfaces:**
- `scripts/verify_docs.py --root PATH` reads a repository root and exits `0` only when the documentation contract passes; omitted `--root` uses the current repository.
- The verifier reports each failure with a repository-relative path and exits nonzero without modifying files.
- The test module uses only `unittest` and temporary directories; it does not require project dependencies.

- [ ] **Step 1: Write focused verifier tests**

  Add tests named `test_accepts_valid_documentation_fixture`, `test_rejects_missing_required_file`, `test_rejects_broken_relative_markdown_link`, `test_rejects_invalid_locale_tag`, `test_rejects_secret_like_added_text`, and `test_rejects_missing_heading`. The fixture must include a valid `README.md`, `LICENSE`, `docs/INDEX.md`, `docs/I18N.md`, root governance files, GitHub templates, and a relative link target; each negative test removes or corrupts exactly one contract.

- [ ] **Step 2: Run the focused tests and verify the initial failure**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_docs_verifier -v
  ```

  Expected: the tests fail because `scripts/verify_docs.py` does not exist yet.

- [ ] **Step 3: Implement the dependency-free verifier**

  Implement `argparse` handling for `--root`, a fixed required-file list matching this plan, recursive Markdown discovery excluding `.git`, `.venv`, `data`, caches, and generated bytecode, and checks for:

  1. required root, canonical, and GitHub files;
  2. one non-empty level-one heading in every project Markdown file;
  3. relative Markdown links that resolve from the source file, ignoring URL, mailto, fragment-only, and external links;
  4. BCP 47 examples matching the documented `en-US`/`th-TH` contract;
  5. forbidden added patterns for private keys, bearer/token assignments, obvious secret assignments, browser storage state, and absolute `/home/` or `/run/` paths in newly added documentation;
  6. YAML template presence and non-empty required fields using a conservative text contract that does not require PyYAML.

- [ ] **Step 4: Run the focused tests and verifier fixture**

  Run the focused test command again and then:

  ```bash
  python3 scripts/verify_docs.py --root /tmp/zmovie-docs-fixture
  ```

  Expected: all focused tests pass and the valid fixture exits `0`.

- [ ] **Step 5: Commit the verifier slice with GPG**

  ```bash
  git add scripts/verify_docs.py tests/test_docs_verifier.py
  git diff --cached --check
  git commit --gpg-sign=220A4C8CCC7D2D50 -m "test: add documentation contract verifier"
  git verify-commit HEAD
  ```

## Task 2: Add root governance and GitHub community documents

**Files:**
- Create: `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, `CHANGELOG.md`
- Create: `.github/CODEOWNERS`, `.github/pull_request_template.md`, `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/ISSUE_TEMPLATE/feature_request.yml`, `.github/ISSUE_TEMPLATE/config.yml`, `.github/dependabot.yml`

**Interfaces:**
- GitHub renders the Markdown community files and templates directly.
- Public issue forms collect redacted reproduction data and route suspected vulnerabilities to `SECURITY.md`.
- Dependabot updates only the declared pip, Docker, and GitHub Actions ecosystems on a weekly schedule.

- [ ] **Step 1: Add the complete MIT license**

  Use the standard MIT text, with the approved `Copyright (c) 2026 cvsz` notice, and do not add restrictions that contradict MIT.

- [ ] **Step 2: Add contribution and conduct guidance**

  Document repository setup with `python3 -m venv`, `python3 -m pip install -r requirements.txt`, the isolated test requirement, `make check`, `git diff --check`, documentation/i18n review, no-secret handling, and signed commits. Use Contributor Covenant reporting language that directs conduct reports privately to repository maintainers without publishing a personal credential or requiring a public issue.

- [ ] **Step 3: Add security and support routing**

  State supported-branch expectations, private vulnerability reporting through GitHub’s security channel or maintainers, no public disclosure of exploit details, and safe handling of `ZMOVIE_SECRET_KEY`, Bilibili browser state, tokens, logs, and local paths. Route ordinary usage questions and reproducible defects to the appropriate issue/template path.

- [ ] **Step 4: Add GitHub templates and dependency metadata**

  Make the bug form require version, deployment mode, reproduction steps, expected/actual behavior, redacted logs, and a secret-safety confirmation. Make the feature form require problem, proposed behavior, scope, acceptance criteria, and documentation/i18n impact. Disable unstructured blank issues while linking `SECURITY.md` and `SUPPORT.md`. Set `* @cvsz` in CODEOWNERS and configure weekly `pip`, `docker`, and `github-actions` updates.

- [ ] **Step 5: Run repository contract checks**

  Run:

  ```bash
  python3 scripts/verify_docs.py
  git diff --check
  ```

  Expected: the verifier may still report missing canonical guides from Task 3, but it must report no malformed root/GitHub file, secret-like content, or invalid template structure.

- [ ] **Step 6: Commit the governance slice with GPG**

  ```bash
  git add LICENSE CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md SUPPORT.md CHANGELOG.md .github/CODEOWNERS .github/pull_request_template.md .github/ISSUE_TEMPLATE .github/dependabot.yml
  git diff --cached --check
  git commit --gpg-sign=220A4C8CCC7D2D50 -m "docs: add project and GitHub governance"
  git verify-commit HEAD
  ```

## Task 3: Add canonical project guides and the i18n standard

**Files:**
- Create: `docs/INDEX.md`, `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/CONFIGURATION.md`, `docs/OPERATIONS.md`, `docs/TROUBLESHOOTING.md`, `docs/TESTING.md`, `docs/RELEASE.md`, `docs/STATUS.md`, `docs/I18N.md`, `docs/DOCUMENTATION_STANDARD.md`, `docs/FAQ.md`
- Modify: `README.md`

**Interfaces:**
- `README.md` links users to `docs/INDEX.md` and current canonical guides.
- `docs/I18N.md` is normative for future UI/API localization but reports current runtime localization truthfully.
- Canonical guides link to existing focused docs rather than duplicating every provider or publication procedure.

- [ ] **Step 1: Write the documentation map and status vocabulary**

  `docs/INDEX.md` must map user, operator, developer, contributor, maintainer, and reviewer journeys to exact files. `docs/STATUS.md` must define `implemented`, `verified`, `configured`, `render-ready`, `production-ready`, `pending`, `submitted`, `published`, `remotely confirmed`, and `deferred`, with the rule that code or a passing unit test alone does not prove runtime or external publication.

- [ ] **Step 2: Write architecture, API, and configuration guides**

  Describe `main:app`, the legacy prompt boundary, `/api/v2`, SQLite persistence, managed media roots, provider routing, FFmpeg validation, publication approval, native systemd paths, Docker paths, environment precedence, and authentication. API examples must use redacted placeholders and must never expose server-local file paths or real credentials.

- [ ] **Step 3: Write operations, troubleshooting, testing, and release guides**

  Cover native and Docker install/upgrade, `status`, `health`, `doctor`, backup/restore, logs, ComfyUI and stable-diffusion.cpp readiness, Bilibili approval gates, evidence-first troubleshooting, the isolated dependency environment, `make check`, CI quality jobs, GPG verification, remote SHA checks, hosted CI, and external/runtime acceptance boundaries.

- [ ] **Step 4: Write the i18n standard**

  Document BCP 47 tags, `en-US` source/default, `th-TH` first additional locale, catalog key naming, ICU interpolation/plural/select, exact→language→`en-US` fallback, `lang`/`dir`, RTL, accessibility, `Intl` formatting, timezone/currency preservation, `Accept-Language`, stable API error codes, catalog parity, placeholder parity, translation review, and the explicit fact that the current UI remains English-only.

- [ ] **Step 5: Write documentation rules and FAQ**

  Define Markdown headings, audience labels, relative links, safe command examples, evidence boundaries, terminology, no-secret rules, i18n references, and how to update a focused guide. The FAQ must answer why mock output is not AI-video evidence, what production readiness requires, how Bilibili publication differs from submission, and which deployment path to choose.

- [ ] **Step 6: Add README navigation without overstating status**

  Keep the existing verified status table and external-gate caveats, add a documentation map near the top, link canonical guides, keep the MIT license section accurate, and state that i18n is a documented standard rather than an implemented localization layer.

- [ ] **Step 7: Run canonical-document checks**

  Run:

  ```bash
  python3 scripts/verify_docs.py
  git diff --check
  ```

  Expected: required-file, heading, relative-link, locale-contract, and secret/path checks pass.

- [ ] **Step 8: Commit the canonical-guide slice with GPG**

  ```bash
  git add README.md docs/INDEX.md docs/ARCHITECTURE.md docs/API.md docs/CONFIGURATION.md docs/OPERATIONS.md docs/TROUBLESHOOTING.md docs/TESTING.md docs/RELEASE.md docs/STATUS.md docs/I18N.md docs/DOCUMENTATION_STANDARD.md docs/FAQ.md
  git diff --cached --check
  git commit --gpg-sign=220A4C8CCC7D2D50 -m "docs: add canonical project guides"
  git verify-commit HEAD
  ```

## Task 4: Normalize the existing Markdown corpus

**Files:**
- Modify: every existing project `*.md` that needs a navigation, terminology, status, command, safety, i18n, or link correction, including `README.md`, focused `docs/*.md`, `docs/evidence/*.md`, `prompts/*.md`, `workflows/*/*.md`, and `zmovie_platform/*.md`.
- Preserve in meaning: `docs/evidence/*.md` and historical `docs/superpowers/{plans,specs}/*.md`.

**Interfaces:**
- Existing focused guides remain deep links from `docs/INDEX.md` and relevant canonical guides.
- Evidence files continue to describe the observation and its boundary at the time recorded.
- No Markdown update changes an API, CLI, environment variable, or runtime behavior.

- [ ] **Step 1: Classify every Markdown file**

  Build an inventory grouped as entry point, canonical guide, focused guide, evidence, prompt/workflow reference, module map, roadmap, or historical plan/spec. Record the classification in `docs/INDEX.md` or its linked inventory and identify the source of truth for commands and status claims.

- [ ] **Step 2: Correct navigation and terminology**

  Add the appropriate canonical-guide link to each focused document, standardize `main:app`, `/opt/zmovie`, `/var/lib/zmovie`, Docker, provider, media, and publication terminology, and remove references that imply the old entry-point integration is still pending when the current source proves otherwise.

- [ ] **Step 3: Correct status and security language**

  Preserve genuine pending/deferred/external gates, distinguish smoke/mock/configured/readiness states from production evidence, remove unsafe secret/path examples, and retain the Cloudflare source-of-truth caveat where it describes a separate infrastructure repository.

- [ ] **Step 4: Add i18n and documentation-standard references**

  Update documents that discuss UI text, API messages, language, Thai voice/content, or future localization to link `docs/I18N.md`. Update contribution, testing, operations, release, and workflow docs to link `docs/DOCUMENTATION_STANDARD.md` where maintenance rules apply.

- [ ] **Step 5: Re-run link and content verification**

  Run:

  ```bash
  python3 scripts/verify_docs.py
  git diff --check
  rg -n -i "TODO|TBD|FIXME|known secret|password=|token=|storage_state\.json" --glob '*.md' --glob '!docs/superpowers/**'
  ```

  Expected: the verifier and whitespace check pass; the final search returns only intentionally documented safe terms, with no credential values or unresolved repository-owned placeholders.

- [ ] **Step 6: Commit the Markdown normalization slice with GPG**

  ```bash
  git add README.md docs prompts workflows zmovie_platform
  git diff --cached --name-only
  git diff --cached --check
  git commit --gpg-sign=220A4C8CCC7D2D50 -m "docs: normalize project documentation"
  git verify-commit HEAD
  ```

  Before committing, confirm `.env.mikrotik.stage` is absent from the staged file list.

## Task 5: Integrate the verifier into GitHub CI

**Files:**
- Modify: `.github/workflows/test.yml`

**Interfaces:**
- The existing Python matrix, Docker job, quality job, shell checks, JavaScript checks, and project tests remain present.
- CI runs `python scripts/verify_docs.py` from the repository root after checkout and before reporting the workflow green.

- [ ] **Step 1: Add the documentation verification step**

  Add a named step under the existing Python job after checkout and before dependent runtime checks:

  ```yaml
      - name: Validate documentation
        run: python scripts/verify_docs.py
  ```

  Keep `permissions: contents: read` and do not remove any existing job or gate.

- [ ] **Step 2: Validate workflow and documentation contracts locally**

  Run:

  ```bash
  python3 scripts/verify_docs.py
  git diff --check
  bash -n scripts/verify_docs.py
  ```

  Do not use `bash -n` as a Python validator; use it only if the verifier is intentionally shipped as a shell script. For this plan the verifier is Python, so validate it with:

  ```bash
  python3 -m py_compile scripts/verify_docs.py
  ```

- [ ] **Step 3: Commit the CI slice with GPG**

  ```bash
  git add .github/workflows/test.yml
  git diff --cached --check
  git commit --gpg-sign=220A4C8CCC7D2D50 -m "ci: verify documentation contracts"
  git verify-commit HEAD
  ```

## Task 6: Run the complete verification and synchronize safely

**Files:**
- Modify: none unless a verification failure requires a targeted documentation correction.

**Interfaces:**
- The final local tree contains only intended documentation, GitHub metadata, verifier, tests, and signed commits.
- Remote synchronization is fast-forward-only and never force-pushes or stages `.env.mikrotik.stage`.

- [ ] **Step 1: Inspect the complete diff and staged/worktree scope**

  Run:

  ```bash
  git status --short --branch
  git diff origin/main...HEAD --stat
  git diff origin/main...HEAD --check
  git diff origin/main...HEAD --name-only
  ```

  Confirm the untracked `.env.mikrotik.stage` is not part of the diff and no generated cache, database, media, or environment file is included.

- [ ] **Step 2: Run documentation and focused verification**

  Run:

  ```bash
  python3 scripts/verify_docs.py
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_docs_verifier -v
  git diff --check
  ```

  Expected: all documentation checks pass with exit code `0`.

- [ ] **Step 3: Run the full declared dependency suite in isolation**

  Use an isolated environment outside the repository, install `requirements.txt`, and run the repository’s documented `make check`, focused Ruff/dependency checks when available, Docker Compose validation, and the project tests. Do not claim the current system interpreter is green when it lacks `edge_tts` or cannot write its root-owned bytecode caches.

- [ ] **Step 4: Verify every new commit signature**

  Run:

  ```bash
  git log --format='%H' origin/main..HEAD | while read -r commit; do git verify-commit "$commit"; done
  git log --show-signature --format='%h %G? %GK %s' origin/main..HEAD
  ```

  Expected: every new commit reports a valid signature from key `220A4C8CCC7D2D50`.

- [ ] **Step 5: Fetch remote state and choose a safe integration path**

  ```bash
  env -u GITHUB_TOKEN git fetch origin
  git rev-parse HEAD origin/main
  git log --oneline --decorate origin/main..HEAD
  git log --oneline --decorate HEAD..origin/main
  ```

  If `origin/main` moved, rebase or merge only with explicit review and rerun all checks. Never force-push. If direct main push is protected, push a topic branch and open a pull request instead of bypassing required checks.

- [ ] **Step 6: Push only after all local gates pass**

  For an authorized direct-main path:

  ```bash
  env -u GITHUB_TOKEN git push origin HEAD:refs/heads/main
  ```

  For a protected-main path, push the signed topic branch and use the repository’s pull-request workflow. Do not report hosted completion until GitHub Actions has passed for the exact pushed SHA.

- [ ] **Step 7: Re-query and report final state**

  ```bash
  env -u GITHUB_TOKEN git fetch origin
  git rev-parse HEAD origin/main
  git status --short --branch
  ```

  Report separately: files changed, documentation verifier result, full project-suite result, commit signatures, remote SHA, hosted CI result, preserved untracked files, and remaining runtime/external gates.

## Plan self-review

- Spec coverage: the plan includes root/GitHub documents, canonical project guides, i18n rules, all-Markdown review, evidence/status boundaries, link and secret checks, CI integration, MIT licensing, GPG commits, remote synchronization, and the known dependency-environment limitation.
- Placeholder scan: no unfilled implementation steps are used; every command names an exact path or contract.
- Type/interface consistency: `scripts/verify_docs.py --root PATH`, `tests.test_docs_verifier`, the required-file contract, and the CI invocation use the same interface.
- Scope boundary: this plan documents runtime localization but does not implement a localization layer; it does not publish external media, alter Cloudflare infrastructure, or commit environment state.
