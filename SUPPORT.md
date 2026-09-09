# Support

## Choose the right channel

- For a reproducible defect, use the
  [bug report form](https://github.com/cvsz/zmovie/issues/new?template=bug_report.yml).
- For a scoped improvement, use the
  [feature request form](https://github.com/cvsz/zmovie/issues/new?template=feature_request.yml).
- For general usage questions, first read the
  [documentation index](docs/INDEX.md), [FAQ](docs/FAQ.md), and
  [troubleshooting guide](docs/TROUBLESHOOTING.md), then open a redacted issue
  only when the available templates fit the question.
- For a security vulnerability or exposed credential, follow
  [SECURITY.md](SECURITY.md) and use a private channel. Never open a public
  issue with the sensitive details.

## Include useful context

For a normal support request, include:

- the zMovie commit or deployment version;
- native systemd, Docker, or local-development mode;
- operating system, Python, Node.js, Docker, and FFmpeg versions when
  relevant;
- the exact safe command or endpoint used;
- expected and observed behavior;
- a minimal reproduction; and
- redacted logs with credentials, browser state, tokens, personal data, and
  private host details removed.

Do not attach databases, media packages, browser profiles, environment files,
or raw production logs unless they have been sanitized and are necessary to
reproduce a non-sensitive defect.

## Support boundaries

The maintainers can help with repository behavior and documented workflows.
Real AI-video throughput, provider availability, Cloudflare account state,
Bilibili account state, platform UI changes, and production infrastructure may
require operator or vendor evidence. A passing local test does not establish
those external conditions.
