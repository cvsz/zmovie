# Documentation Standard

This document defines the writing and maintenance rules for zMovie project
documentation. The [documentation index](INDEX.md) is the navigation entry
point; the root [README](../README.md) remains the shortest product overview.

## Structure and navigation

- Give every Markdown document one meaningful level-one heading.
- Use headings in a logical order and keep sections short enough to scan.
- Link to canonical guides rather than duplicating operational procedures.
- Prefer repository-relative links for files and stable HTTPS links for external
  standards or services.
- Add new user, operator, developer, and maintainer documents to
  [`INDEX.md`](INDEX.md).

## Truthful status and evidence

Describe the state that was actually verified. Use the vocabulary in
[`STATUS.md`](STATUS.md): implemented code, local verification, runtime
verification, external confirmation, and deferred work are different claims.
Include a date, command, endpoint, or artifact when it materially supports a
claim. Do not turn a plan, mock provider, browser submission, or generated
brief into production evidence.

Historical evidence may remain useful, but label its time and scope clearly.
When current behavior differs, update the canonical guide and link to the
historical record instead of silently rewriting history.

## Commands and examples

- Show commands from the repository root unless another directory is required.
- Prefer `python3` and explicit virtual-environment commands in new examples.
- Explain required environment variables without including their values.
- Keep examples safe to copy: use placeholders for credentials, URLs, IDs, and
  machine-specific paths.
- State whether an operation is read-only, local-only, staging, or an external
  publication action.

## Security and privacy

Follow [`SECURITY.md`](../SECURITY.md). Never commit passwords, API tokens,
private keys, browser profiles, 2FA codes, cookies, or production-only paths.
Use fake or redacted identifiers in evidence. If a procedure needs a secret,
document the variable name, scope, and rotation path—not the secret itself.

## Internationalization and language

All user-facing localization guidance belongs in [`I18N.md`](I18N.md). Use
BCP 47 locale tags, stable message keys, explicit fallback behavior, and
locale-aware formatting. New UI strings should be catalog-ready even while the
current UI is English-only. Keep technical identifiers, commands, endpoint
names, and environment variable names unchanged across translations.

## Maintenance and review

When behavior, configuration, APIs, release gates, or security boundaries
change, update the affected canonical guide in the same change. Review links,
commands, status labels, and examples before merging. Run:

```bash
python3 scripts/verify_docs.py
python3 -m unittest tests.test_docs_verifier -v
```

Documentation changes should explain what readers can do now and what remains
unverified. For contribution expectations, see [`CONTRIBUTING.md`](../CONTRIBUTING.md).
