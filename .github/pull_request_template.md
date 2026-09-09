# Pull request template

## Summary

<!-- Explain the user or maintainer problem and the resulting change. -->

## Scope checklist

- [ ] The change is limited to the stated scope.
- [ ] No credentials, browser state, tokens, databases, media, generated files,
      or private host paths are included.
- [ ] Existing authentication, ownership, approval, idempotency, and fail-closed
      boundaries remain intact.

## Documentation and i18n

- [ ] Relevant canonical and focused Markdown docs are updated.
- [ ] Relative links and command examples are valid.
- [ ] User-facing language follows `docs/I18N.md`, including locale tags,
      placeholders, formatting, fallback, and accessibility requirements.
- [ ] The change does not claim runtime localization or production readiness
      without evidence.

## Verification

- [ ] Focused tests or checks were run and their result is recorded below.
- [ ] `git diff --check` passes.
- [ ] Documentation verification was run when documentation or GitHub metadata
      changed.
- [ ] Hosted CI, runtime evidence, and external publication evidence are
      distinguished from local checks.

## Verification notes

<!-- List exact commands and observed results. Say Not run with a reason when a
     check is unavailable. Do not include secrets or unredacted logs. -->
