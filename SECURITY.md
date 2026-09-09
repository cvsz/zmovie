# Security policy

## Supported source

The `main` branch is the current supported source line. There is no published
release support matrix yet. Operators should deploy a reviewed commit and keep
the native installation or container updated through the documented upgrade
path.

## Reporting a vulnerability

Please report suspected vulnerabilities privately through
[GitHub private vulnerability reporting](https://github.com/cvsz/zmovie/security/advisories/new)
when it is available, or contact the repository maintainers through GitHub's
private contact mechanism. Do not open a public issue, include exploit details
in a pull request, or paste sensitive data into chat.

Include only the minimum redacted information needed to reproduce the issue:

- affected commit or deployment version;
- deployment mode and relevant operating-system/runtime details;
- a concise impact description;
- safe reproduction steps or a minimal non-destructive proof; and
- the logs or traces needed to confirm the behavior with credentials and
  personal data removed.

The maintainers will acknowledge a report when practical, validate the impact,
coordinate a fix or mitigation, and disclose the issue after a safe correction
and affected operators have had reasonable notice. This project does not
promise a fixed response or disclosure timetable.

## Sensitive material

Treat the following as credentials or sensitive operational state:

- `ZMOVIE_SECRET_KEY` and generated administrator credentials;
- GitHub, Cloudflare, renderer, TTS, and other provider credentials;
- Bilibili Playwright browser storage state, cookies, local storage, and
  IndexedDB;
- private media, export packages, databases, logs, and backup files; and
- private hostnames, network topology, and unredacted API responses.

Never commit or share those values. Use a secret manager or operator-controlled
environment and redact logs before attaching them to an issue or pull request.
The GitHub environment helper documents metadata-only handling; GitHub does not
return secret values for export.

## Security boundaries

Authentication, project ownership, managed media roots, approval gates,
idempotency, and fail-closed publication behavior are security boundaries.
Model-free smoke output and the mock provider are not proof of production
inference or publication safety. Public reachability also does not prove that
every application route is safe for internet exposure; retain authentication,
TLS/reverse-proxy controls, and the external publication approval gate.

## Dependency and workflow reports

Dependency vulnerabilities and GitHub Actions concerns should be reported
privately when they expose an exploitable path. Routine upgrade proposals may
use Dependabot or a pull request after confirming compatibility with the
supported Python matrix, Docker build, shell checks, and production boundaries.
