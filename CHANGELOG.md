# Changelog

All notable repository changes are recorded here. Entries describe committed
repository behavior and do not substitute for hosted CI, deployment evidence,
or external publication confirmation.

## Unreleased

### Added

- Explicit Studio-to-Cinema import boundary (`zmovie_platform/studio_cinema.py`,
  `cinema_import_routes.py`): QC, rights confirmation, human approval,
  idempotent imports, audit trail; render success never auto-publishes;
- Commerce sandbox foundation (`zmovie_platform/commerce/`): plans,
  subscriptions, entitlements, sandbox PSP checkout, signed idempotent
  webhooks, append-only ledger, refunds, reconciliation; live PSP blocked;
- Separate ticketing domain (`zmovie_platform/ticketing/`,
  `services/cinema-api/`): branches, halls, seat maps, atomic holds,
  idempotent reservations with DB-level no-double-sell, signed QR check-in,
  cancel/refund states; synthetic seed only, no live sales;
- Privacy export (redacted) and explicit-confirm account deletion
  (`zmovie_platform/privacy.py`, `/api/v2/privacy/*`);
- Liveness/readiness probes (`/api/v2/livez`, `/api/v2/readyz`),
  deployment smoke and backup/license health scripts, versioned
  Nginx/cloudflared examples, deployment + WordPress backup/restore runbooks;
- Security: threat model, Ed25519 license key management, secret-scan CI,
  cross-cutting regression tests; and
- Production evidence set: feature matrix, test evidence, rollback evidence,
  architecture ADRs, current-state index;
- Hyperframes creative template catalog and Studio/CLI integration;
- managed MP4 previews, project reset safeguards, hardened Bilibili package
  approval/preflight flow, and production evidence documents; and
- repository documentation and GitHub governance baseline, including the
  multilingual i18n standard.

### Status boundaries

- Real accelerated video throughput remains dependent on an operator-supplied
  compatible model and renderer environment.
- Bilibili submission is not public publication; completion still requires a
  confirmed public URL and durable remote confirmation.
- YouTube publishing remains intentionally deferred. See
  [docs/YOUTUBE_ROADMAP.md](docs/YOUTUBE_ROADMAP.md).

Future entries should name the user-facing or maintainer-facing change, link to
the relevant guide when useful, and avoid claiming a release or runtime result
that has not been verified.
