# zMovie Documentation and GitHub Baseline

**Date:** 2026-09-09
**Status:** Approved design; implementation follows after spec review

## Goal

Make zMovie understandable and maintainable for users, operators, developers,
contributors, and GitHub reviewers. The work adds the missing project and
GitHub documents, reviews every existing Markdown file, establishes one
truthful status vocabulary, and defines a repository-wide internationalization
(i18n) standard without claiming that runtime localization already exists.

## Current evidence

- The repository contains 87 Markdown files and has no broken relative Markdown
  links in the current checkout.
- The root README and `zmovie_platform/README_*.md` files contain substantial
  implementation, deployment, API, security, and operational material, but
  there is no central documentation index or canonical audience map.
- `.github/` currently contains only `workflows/test.yml`.
- GitHub Community Health reports 14% and identifies missing code of conduct,
  contributing guide, issue template, license, and pull-request template.
- The current static UI uses English markup and hard-coded strings; no runtime
  locale catalog or localization layer is currently implemented.

## Decisions

- Use the MIT License with `Copyright (c) 2026 cvsz`.
- Keep technical documentation, code comments, keys, and configuration names
  in English. Examples may include Thai content where the product workflow
  requires it.
- Use `en-US` as the default locale and `th-TH` as the first additional locale
  in the i18n standard. Additional locales must follow the same contract.
- Treat `docs/INDEX.md` and the root `README.md` as navigation documents. Keep
  detailed module README files where they are useful, and link them from the
  canonical guides instead of silently deleting or merging them.
- Preserve the distinction between implemented behavior, verified runtime
  evidence, pending external acceptance, and intentionally deferred roadmap
  work.
- Do not add secrets, browser state, tokens, private host paths, or copied
  environment values to any document, template, example, or commit.
- Do not rewrite historical commits. Any new commits for this work use the
  configured GPG signing key.

## Documentation architecture

### Root and GitHub entry points

Add or maintain:

- `README.md` — concise product overview, verified status, quickstarts, and
  links to canonical guides.
- `LICENSE` — complete MIT license text.
- `CONTRIBUTING.md` — development setup, quality gates, documentation and i18n
  workflow, security rules, and signed-commit expectations.
- `CODE_OF_CONDUCT.md` — Contributor Covenant with private reporting guidance.
- `SECURITY.md` — vulnerability reporting, supported versions, credential and
  browser-state handling, and safe disclosure boundaries.
- `SUPPORT.md` — routing for usage questions, reproducible bugs, feature
  requests, and security reports.
- `CHANGELOG.md` — evidence-backed `Unreleased` history and future release
  conventions; no invented version or publication claims.

### Canonical project guides

Add:

- `docs/INDEX.md` — audience-based map of all project documentation.
- `docs/ARCHITECTURE.md` — service entry point, legacy/v2 boundary, storage,
  providers, pipeline, publication gates, and deployment surfaces.
- `docs/API.md` — v2 and compatibility API map, authentication, response
  boundaries, and examples that do not expose local paths.
- `docs/CONFIGURATION.md` — environment variables, defaults, precedence,
  native versus Docker paths, renderer configuration, and secret handling.
- `docs/OPERATIONS.md` — install, upgrade, status, health, backup, restore,
  logs, renderer readiness, and safe production workflow.
- `docs/TROUBLESHOOTING.md` — failure symptoms, evidence-first diagnosis,
  permissions, dependency setup, network boundaries, and recovery paths.
- `docs/TESTING.md` — local and CI gates, isolated dependency environments,
  syntax checks, security checks, Compose validation, and known environment
  prerequisites.
- `docs/RELEASE.md` — signed commit, review, verification, push, CI, and
  external/runtime evidence requirements.
- `docs/STATUS.md` — single status vocabulary and current implementation,
  verified, pending, deferred, and external-gate classifications.
- `docs/I18N.md` — normative multilingual UI/API/documentation standard.
- `docs/DOCUMENTATION_STANDARD.md` — Markdown structure, links, examples,
  evidence, terminology, security, and maintenance rules.
- `docs/FAQ.md` — concise answers for installation, providers, production
  readiness, Bilibili publication, and the mock-provider boundary.

Existing focused guides such as Bilibili, ComfyUI, stable-diffusion.cpp,
Hyperframes, evidence, prompts, workflows, and module READMEs remain part of
the documentation set. They receive links, terminology, status, and command
corrections where needed.

## i18n standard

`docs/I18N.md` defines a future-proof contract and must not imply that current
screens are localized.

### Locale and language identifiers

- Use valid BCP 47 tags, with canonical casing: `en-US`, `th-TH`, and so on.
- Use `en-US` as the source/default locale and register every supported locale
  explicitly.
- Set the document `lang` attribute and the effective text direction from the
  active locale. Do not infer direction from user-entered content.
- Use locale-aware formatting for dates, times, numbers, currencies, lists, and
  relative time; never format these with string concatenation.

### Message catalogs and code

- Keep user-facing strings in locale catalogs with stable, namespaced keys such
  as `studio.project.create`.
- Use ICU-style interpolation, plural, and select messages where the runtime
  supports them. Preserve variable names and types across all translations.
- Never use translated text as a key, concatenate sentence fragments, or embed
  secrets and machine paths in a message.
- Keep labels, help text, errors, validation messages, accessibility names, and
  empty/loading states inside the same translation contract.
- Treat developer logs, API field names, environment variables, CLI flags, and
  persisted identifiers as stable English technical contracts unless an
  explicit localized presentation field is defined.

### Fallback, accessibility, and API behavior

- Resolve locale in this order: exact locale, language-only locale, then
  `en-US`.
- Missing keys must be detectable in development and CI and must fall back
  safely in production without exposing raw key names to users.
- Preserve keyboard navigation, screen-reader names, text expansion space,
  plural correctness, and RTL layout behavior.
- API clients may send `Accept-Language`; services must validate the tag and
  return a documented, deterministic fallback. Error codes remain stable while
  human-readable messages may be localized.
- Dates and timestamps must include an explicit timezone policy. Currency and
  numeric formatting must never change the underlying stored value.

### Translation workflow and quality gates

- A source-message change updates every catalog in the same change or records a
  deliberate fallback decision.
- CI checks locale-tag validity, key parity, duplicate keys, placeholder parity,
  plural/select structure, and JSON syntax.
- Reviewers verify Thai text and other translations for meaning, tone, length,
  safety, and platform constraints; machine translation is not treated as
  final review.
- Documentation examples use locale-neutral technical identifiers and clearly
  label user-facing localized examples.

## GitHub governance

Add the following repository-owned GitHub files:

- `.github/CODEOWNERS` with `@cvsz` as the default owner.
- `.github/pull_request_template.md` covering scope, tests, docs, i18n,
  security, secrets, runtime evidence, and external-gate claims.
- `.github/ISSUE_TEMPLATE/bug_report.yml` for reproducible defects.
- `.github/ISSUE_TEMPLATE/feature_request.yml` for scoped proposals and
  acceptance criteria.
- `.github/ISSUE_TEMPLATE/config.yml` disabling unstructured blank issues and
  linking security/support guidance.
- `.github/dependabot.yml` for weekly `pip`, Docker, and GitHub Actions updates.

Public issue forms must redirect suspected vulnerabilities to `SECURITY.md`.
The templates must request versions, environment, reproduction steps, and
redacted logs without requesting credentials or browser storage.

## Existing Markdown update policy

Every existing `*.md` file is reviewed. Changes are made when a file has a
broken navigation path, stale entry-point claim, inconsistent status, unsafe
example, missing i18n/documentation-standard link, contradictory command, or
terminology drift. A correct focused document is not rewritten merely to
produce diff noise.

The update must:

1. link each audience to the canonical guide and preserve useful deep links;
2. standardize `main:app`, native `/opt/zmovie`, Docker, and `/var/lib/zmovie`
   terminology according to the actual deployment path;
3. label mock, smoke, configured, render-ready, production-ready, submitted,
   published, and remotely confirmed states precisely;
4. keep evidence files immutable in meaning and distinguish historical caveats
   from current source-of-truth claims;
5. remove secrets and private machine details from examples while retaining
   safe placeholders;
6. add i18n references where user-facing text, API messages, or future locale
   behavior is discussed; and
7. maintain zero broken relative links.

## Verification

Add a dependency-free documentation verifier that checks required files,
relative links, Markdown headings, template presence, locale-tag examples, and
forbidden secret/path patterns in newly added documentation. Wire it into the
existing GitHub workflow without removing the Python matrix, Docker, quality,
or security gates.

Run locally:

```bash
python3 scripts/verify_docs.py
git diff --check
```

Also run the project’s documented checks in an isolated environment with the
declared dependencies, then validate GitHub YAML structure and inspect the
staged file list. The current system environment is not a valid substitute for
the declared dependency set when optional production modules are imported.

## Acceptance criteria

- All current Markdown files have been reviewed and relevant updates are
  applied without deleting useful evidence or inventing completion claims.
- The required root and GitHub governance files exist and use MIT licensing,
  safe reporting, and redacted examples.
- Canonical project guides and the i18n standard are linked from `README.md` and
  `docs/INDEX.md`.
- Documentation verification reports no broken relative links, missing required
  files, invalid locale examples, or secret-bearing additions.
- The i18n guide clearly separates the standard from runtime localization that
  is not yet implemented.
- Local verification, GPG signatures, remote synchronization, and hosted CI are
  reported separately; none is inferred from the others.
