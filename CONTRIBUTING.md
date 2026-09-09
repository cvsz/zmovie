# Contributing to zMovie

Thank you for helping improve zMovie. Contributions should make the project
safer, easier to operate, and more truthful about the boundary between a local
workflow and externally verified production.

## Before opening a change

1. Read the [documentation index](docs/INDEX.md),
   [documentation standard](docs/DOCUMENTATION_STANDARD.md),
   [security policy](SECURITY.md), and [i18n standard](docs/I18N.md).
2. Search existing issues and pull requests before proposing duplicate work.
3. Keep the change focused. Separate unrelated refactors, generated files,
   local configuration, databases, media, browser state, and credentials from
   the patch.
4. For a security concern, follow [SECURITY.md](SECURITY.md) instead of opening
   a public issue.

## Development setup

Use Python 3.11 through 3.14 as supported by CI and create an isolated
environment. The repository uses `python3` explicitly in contributor commands:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip wheel
./.venv/bin/python -m pip install -r requirements.txt
```

Install Playwright Chromium only when browser or publication tests require it:

```bash
PLAYWRIGHT_BROWSERS_PATH=.playwright \
  ./.venv/bin/python -m playwright install chromium
```

Do not commit `.venv`, `.playwright`, `data`, browser storage state, or local
environment files. If the checkout contains root-owned Python caches, use an
isolated bytecode prefix for local checks rather than changing unrelated host
ownership:

```bash
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m unittest discover -s tests -v
```

## Required checks

Run the checks relevant to the changed surface from the repository root:

```bash
make check
make lint
make audit
docker compose config --quiet
python3 scripts/verify_docs.py
git diff --check
```

`make audit` and optional quality tools may require their documented packages.
Report unavailable tools explicitly. A green unit suite does not prove real
video inference, public publication, Cloudflare routing, or production
certification.

## Documentation changes

Every Markdown change must follow [DOCUMENTATION_STANDARD.md](docs/DOCUMENTATION_STANDARD.md).
Update the canonical guide and the focused guide when a command or contract
changes. Use relative links, safe redacted examples, and evidence-backed status
labels. Keep historical evidence and approved plans accurate rather than
rewriting their observations.

For user-facing language or future localization, follow [I18N.md](docs/I18N.md):
use BCP 47 tags, stable keys, placeholder parity, locale-aware formatting, and
explicit fallback behavior. Do not describe the current English-only UI as
localized.

## Code and security rules

- Preserve authentication, tenant/project ownership, approval gates,
  idempotency, managed media roots, and fail-closed publication behavior.
- Never log, commit, or paste credentials, tokens, browser state, private keys,
  or unredacted production data.
- Do not use the mock provider as evidence of AI-video production readiness.
- Keep public API responses free of server-local paths and secret-bearing
  configuration.
- Add a focused regression test for behavior changes and explain external or
  runtime gates that cannot run locally.

## Commits and pull requests

Use a concise conventional subject such as `docs: clarify backup workflow`.
New commits should be signed with the configured project GPG key:

```bash
git commit --gpg-sign=220A4C8CCC7D2D50 -m "docs: clarify backup workflow"
git verify-commit HEAD
```

Before opening a pull request, inspect the staged file list and confirm that
`.env*`, generated caches, databases, media, browser state, and unrelated
worktree changes are absent. Complete the repository pull-request template and
separate local verification, hosted CI, runtime evidence, and external
publication evidence.
