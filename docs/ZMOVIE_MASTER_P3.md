
# ZEAZDEV ZMOVIE — NEXT MASTER IMPLEMENTATION PROMPT
# Mission: Real Environment Configuration + Remaining Production Features
# Execution: Autonomous, evidence-driven, non-destructive
# Date: 2026-09-24

You are OpenCode, acting as the senior platform architect, security
engineer, SRE, WordPress engineer, Python engineer and QA lead.

Work directly on the operator's local Ubuntu server.
Implement changes, run tests, produce evidence and commit safe
repository changes. Do not stop after writing another master plan.

COMMUNICATION
- Explain and report all work in Thai.
- Keep code, commands, environment variables and configuration in English.
- Follow repository AGENTS.md files.
- Separate implementation evidence from actual runtime verification.
- Never claim a feature is complete merely because code exists.

REPOSITORIES

Main application:
  ~/zmovie
  https://github.com/cvsz/zmovie

WordPress setup:
  ~/zmovie-wp-setup

Infrastructure:
  ~/platforms/zworkforce
  https://github.com/cvsz/zworkforce

Cloudflare Terraform:
  ~/platforms/zworkforce/infrastructure/terraform/cloudflare

Known GitHub baselines:
  zmovie/main: db98a96262c5207f0363907487b1f6c13803dbf7
  zworkforce/main: 14e621e3485463844aa71f277c3b0482617150e5

Fetch latest refs before making changes.

Existing public routes:
  https://zmovie.zeaz.dev/
  https://zmovie.zeaz.dev/cinema/

Reported local services:
  zMovie application: 127.0.0.1:8080
  License Server:     127.0.0.1:8085
  Cinema API:         127.0.0.1:8095, if installed
  MariaDB:            127.0.0.1:3306
  Cloudflare Tunnel
  Nginx
  PHP-FPM

Verify actual ownership and process state before acting.

========================================================
PHASE 0 — SAFETY AND CONFIGURATION DISCOVERY
========================================================

Inspect both repositories, Git status, current branches, running
services, deployment scripts and existing tests.

Preserve all local user work.

Identify all REAL runtime environment files, including:

  ~/zmovie/.env

  ~/zmovie-wp-setup/wp-installer/.env
    if this file exists

  WordPress's actual wp-config.php

  PHP-FPM environment and pool configuration

  The running License Server's actual EnvironmentFile

  The running Cinema API's actual EnvironmentFile,
    if the service is installed

  Docker Compose or systemd environment declarations

Do not assume that the installer .env is the runtime environment.

Use safe service and filesystem inspection.

Never print:
  passwords
  API tokens
  license keys
  private signing keys
  full environment files
  systemd configurations containing literal secrets

Collect only configuration paths, variable names, redacted
presence indicators and service health results.

========================================================
PHASE 1 — UPDATE REAL .ENV FILES IN PLACE
========================================================

THIS IS THE HIGHEST-PRIORITY TASK.

Actually modify the existing deployment environment on this
machine. Do not merely update .env.example or write instructions
asking the operator to edit .env manually.

FIRST:
- Discover which env file is consumed by each live service.
- Determine the authoritative secret store.
- Detect duplicate and conflicting definitions.
- Preserve existing valid credentials.
- Validate current hostnames, ports, database and filesystem paths.
- Back up the existing configuration outside the repository
  and outside every public document root.

BACKUP REQUIREMENTS:
- restrictive directory permissions
- private backup file permissions
- no backup committed to Git
- no .env.bak in the web root
- protected backup retention
- recoverable prior version

Use an atomic update:
  validate proposed configuration
  write temporary file in same filesystem
  enforce restrictive permissions
  fsync where appropriate
  atomically replace original
  reload only affected services
  run health tests
  roll back if health checks fail

Do not rewrite or reformat unrelated values unnecessarily.

--------------------------------------------------------
1A. MAIN ZMOVIE ENVIRONMENT
--------------------------------------------------------

Reconcile the existing ~/zmovie/.env against the
actual variables consumed by the application.

Verify the existing names from source before modifying them:

  ZMOVIE_HOST
  ZMOVIE_PORT
  ZMOVIE_DB_PATH
  ZMOVIE_MEDIA_ROOT
  ZMOVIE_EXPORT_ROOT
  ZMOVIE_PUBLISH_ROOT
  ZMOVIE_AUTH_ENABLED
  ZMOVIE_ENABLE_DOCS
  ZMOVIE_SECRET_KEY
  ZMOVIE_ADMIN_USER
  ZMOVIE_ADMIN_PASSWORD
  ZMOVIE_CORS_ORIGINS

Also inspect existing ComfyUI, TTS, Bilibili, object storage
and publishing configuration. Preserve working integrations.

Expected production constraints:

  Application must listen on an approved private interface.
  Authentication must remain enabled.
  CORS must use explicit approved origins.
  Production secrets must not use development defaults.
  Documentation endpoints must follow approved access policy.
  Existing persistent DB/media paths must remain unchanged
  unless a verified migration is performed.

Review the actual parsing format of ZMOVIE_CORS_ORIGINS.
Do not guess whether it expects JSON, CSV or another format.

Provision these additional runtime secrets if their
corresponding features are deployed:

  ZMOVIE_PSP=sandbox
  ZMOVIE_PSP_WEBHOOK_SECRET
  CINEMA_ADMIN_TOKEN
  CINEMA_QR_SECRET

Generate strong independent secrets if missing.

Never reuse the zMovie application secret as:
  a payment webhook secret
  a Cinema administration token
  a QR signing secret
  a License Server signing key

Keep all real payment processing disabled.

Remove insecure development-secret fallbacks from
production execution paths while retaining explicit
test-only configuration.

--------------------------------------------------------
1B. WORDPRESS ENVIRONMENT
--------------------------------------------------------

Discover the actual WordPress document root and runtime
configuration first.

Expected public installation:

  WP_URL=https://zmovie.zeaz.dev/cinema

Expected first-party license origin:

  ZEAZ_LICENSE_ORIGIN=https://zmovie.zeaz.dev

IMPORTANT:
ZEAZ_LICENSE_ORIGIN must match the actual browser origin
expected by the current license verifier. Do not append
/cinema unless the signed-token contract is explicitly
changed and its tests are updated.

Inspect the real WordPress installation settings:

  home
  siteurl
  DB_HOST
  DB_NAME
  DB_USER
  table prefix
  PHP-FPM environment
  active plugin
  active theme

Keep real DB credentials unchanged if they were already
securely rotated and work correctly.

Reconcile the existing installer configuration with the
active installation:

  WP_PATH
  WP_URL
  WP_TITLE
  WP_ADMIN_USER
  WP_ADMIN_EMAIL
  WP_LOCALE
  DB_HOST
  DB_PORT
  DB_NAME
  DB_USER
  DB_PREFIX
  DB_AUTO_CREATE
  VERIFY_CHECKSUMS
  FORCE_CORE_DOWNLOAD
  ZEAZ_LICENSE_API
  ZEAZ_LICENSE_ORIGIN
  ZEAZ_LICENSE_KEY
  ZEAZ_LICENSE_PUBLIC_KEY

On an existing production installation:

  DB_AUTO_CREATE=false
  FORCE_CORE_DOWNLOAD=false
  VERIFY_CHECKSUMS=true

Do not recreate an existing WordPress database.

Do not reset an existing WordPress administrator account.

Improve wp-installer/install.sh so repeat executions do
not require retaining WP_ADMIN_PASSWORD or DB_ROOT_PASSWORD
when WordPress and its database are already installed.

Avoid persisting unnecessary installation-only credentials.

--------------------------------------------------------
1C. ACTUAL WORDPRESS PHP-FPM SECRET DELIVERY
--------------------------------------------------------

The existing installer can generate wp-config.php constants
that call getenv().

This is insufficient unless PHP-FPM actually receives the
configured environment variables.

Inspect:
  the active PHP-FPM service
  pool settings
  clear_env
  systemd environment configuration
  effective service identity

Ensure these variables reach the intended PHP-FPM pool:

  ZEAZ_LICENSE_API
  ZEAZ_LICENSE_ORIGIN
  ZEAZ_LICENSE_KEY
  ZEAZ_LICENSE_PUBLIC_KEY

Do not make secrets available to unrelated PHP applications.

Do not expose them through phpinfo(), diagnostics, REST
responses, application logs, HTML or JavaScript.

If appropriate, use a restricted service-specific environment
file and controlled PHP-FPM pool env declarations.

Keep wp-config.php free of literal license secrets whenever
the approved runtime secret mechanism supports it.

Validate secret availability from within the actual PHP-FPM
execution context, not merely a shell session.

Never display secret values in the validation output.

========================================================
PHASE 2 — FIX LICENSE API HTTPS INTEGRATION
========================================================

The current WordPress license verifier requires HTTPS:

  ZEAZ_LICENSE_API must use https://

The reported License Server currently runs on:

  http://127.0.0.1:8085

Do not set ZEAZ_LICENSE_API to the HTTP loopback address
and claim the integration is operational.

Investigate the real production HTTPS endpoint.

Preferred candidate, only if provisioned and verified:

  https://license.zeaz.dev

If the approved endpoint does not yet exist:

1. Design a secure HTTPS ingress for the existing License Server.
2. Reuse approved Nginx and Cloudflare infrastructure.
3. Make necessary Terraform changes in the appropriate branch.
4. Avoid duplicate DNS records or tunnel routes.
5. Restrict administrative endpoints to trusted access only.
6. Add activation rate limiting and audit logging.
7. Validate TLS and WordPress-to-License-API connectivity.

Do not expose private administrative endpoints publicly
without strong authentication and access controls.

Update ZEAZ_LICENSE_API in the REAL environment only after
the actual HTTPS endpoint passes health and TLS validation.

The public key must be a pinned raw Ed25519 verification key
in the encoding expected by the WordPress plugin.

Verify it against the existing trusted signing key.

Do not replace a trusted pinned key simply because a remote
public-key endpoint returns a different value.

Test actual WordPress-to-License-Server activation:

  valid key
  wrong product
  wrong site
  expired key
  revoked key
  tampered signature
  wrong public key
  missing cinema.creator entitlement

Confirm that invalid entitlements fail closed.

========================================================
PHASE 3 — VERSION THE LICENSE SERVER SOURCE
========================================================

GitHub zmovie/main currently contains services/cinema-api
but the reported running License Server source is not
present under services/license-server in main.

Locate the actual deployed License Server source.

Determine whether it is:
  in another repository
  in another branch
  in a local untracked directory
  installed from a previous source archive
  managed through a system package or container

Do not recreate it blindly if a working implementation exists.

If it is first-party source and suitable for this repository:

  sanitize it
  remove all credentials
  remove private key material
  add an .env.example with no real secrets
  add dependency locks
  add migrations
  add a reproducible installation procedure
  add systemd or container deployment files
  add integration tests
  add backup/restore instructions
  open a focused PR

Preserve the existing signing protocol and active key material.

No secrets, certificate private keys, databases or production
configuration files may enter Git.

========================================================
PHASE 4 — CLOUDFLARE MAIN BRANCH RECONCILIATION
========================================================

The local zworkforce Terraform deployment was reported
as having no drift.

However, the publicly accessible zworkforce/main needs
to be independently reconciled with the deployed
zMovie resource configuration.

Inspect:
  main
  fix/security-production-secrets
  the operator's current local branch
  Terraform state
  live DNS/tunnel resources

Check the actual presence of:
  cloudflare_dns_record.zmovie
  zmovie_hostname
  zmovie_origin
  tunnel ingress configuration

If infrastructure is already working:

  do not duplicate it
  do not replace the live tunnel
  do not modify unrelated DNS resources

Bring the correct reviewed infrastructure configuration
into the approved Git branch through a focused PR.

If resources already exist but are absent from state,
review import instead of creating duplicates.

Require:
  terraform fmt
  terraform validate
  terraform plan

Stop before any unreviewed destructive Terraform apply.

========================================================
PHASE 5 — FIX BASELINE TEST FAILURES
========================================================

Previous evidence reported:

  143 passing tests
  2 errors

The errors were attributed to a missing edge_tts dependency
in the local test environment.

Recreate the test environment from the committed dependency
manifest in an isolated virtual environment.

Run the full test suite.

Determine the actual cause of each error from current logs.

Do not automatically classify failures as pre-existing.

Fix dependency installation, test isolation or actual defects
using the smallest appropriate change.

Also complete the remaining documentation verification errors
without weakening secret detection or path safety rules.

Required outcome:
  full unit suite green
  existing quality checks green
  no regression in zMovie or WordPress
  clean CI evidence

========================================================
PHASE 6 — REAL STAGING ENVIRONMENT
========================================================

Create a real staging environment, separate from production.

Requirements:
  separate database
  separate media paths
  separate environment files
  separate service credentials
  separate License Server test key
  no real card data
  no real live-payment access
  non-production film assets
  controlled public access where needed

Do not clone production user data into staging without an
approved sanitization process.

Add a staging deployment workflow with:

  pinned Git commit
  schema migration
  readiness check
  application smoke tests
  automatic failure detection
  safe rollback procedure

Test all affected services before deployment to production.

========================================================
PHASE 7 — COMPLETE REMAINING FEATURE GATES
========================================================

Use docs/production/FEATURE_MATRIX.md as the existing
requirements register.

Do not rewrite completed Studio, Commerce or Ticketing
modules without a verified defect.

Finish the currently incomplete features:

A. Authenticated Cinema E2E

  real WordPress login
  viewer favorites
  creator submission
  rights confirmation
  pending editorial review
  administrator approval
  invalid-license denials
  logout and session expiry
  concurrent-user permission isolation

B. Membership User Interface

  plan display
  subscription management
  entitlement display
  cancellation
  renewal state
  sandbox checkout
  account privacy controls
  clear payment failure states

C. Media Pipeline

  safe upload validation
  authenticated upload authorization
  FFprobe validation
  real transcoding evidence
  poster generation
  failed-job retries
  object-storage integration
  private media access controls
  media retention and cleanup

Use existing Studio→Cinema approval boundaries.

D. PostgreSQL Readiness

  versioned migrations
  isolated PostgreSQL integration environment
  production-compatible transaction handling
  booking concurrency tests
  migration and rollback tests
  backup and restore evidence

The SQLite sandbox must remain operational until migration
is explicitly approved.

Do not activate live ticket sales.

E. Accessibility

  axe-based automated accessibility checks
  keyboard-only navigation
  screen-reader testing
  focus management
  reduced motion
  contrast
  touch target sizes
  accessible form errors
  multilingual labels

Document actual findings and fixes.

Do not claim WCAG 2.2 AA without sufficient audit evidence.

F. Performance

  baseline latency
  frontend LCP, CLS and INP
  REST performance
  media-processing throughput
  license activation latency
  database performance
  isolated concurrency and soak testing

Propose measurable SLOs for operator approval.

Do not load-test the live public website in a disruptive way.

G. Supply Chain and CI/CD

  SBOM generation
  dependency auditing
  container scanning
  release provenance
  artifact checksums
  release versioning
  staging deployment gate
  production approval gate
  known-good rollback

Keep secrets out of workflow logs and artifacts.

========================================================
PHASE 8 — OPERATIONS AND DISASTER RECOVERY
========================================================

Inspect existing backups and restore evidence.

Do not recreate working backup jobs unnecessarily.

Add recurring, isolated restore validation where safe.

Verify:
  zMovie database
  WordPress MariaDB database
  License Server database
  Ticketing and Commerce data stores
  media assets
  protected key recovery
  application configuration
  release artifacts

Never restore into the production database during a drill.

Recheck:
  daily cron
  backup retention
  off-host copies
  encryption
  integrity
  disk utilization
  recovery metrics
  restore alerts
  failed backup alerts

Validate:
  WordPress rollback
  zMovie rollback
  License Server rollback
  database migration rollback
  Terraform configuration rollback

Record measured evidence, not estimated completion claims.

========================================================
PHASE 9 — FINAL ENVIRONMENT VERIFICATION
========================================================

After updating the REAL .env files, perform these checks:

1. Correct service identity and file permissions.
2. No duplicate or conflicting environment definitions.
3. No unresolved example.com endpoints in live configuration.
4. Real WordPress runtime sees required License variables.
5. WordPress and License Server use the same token contract.
6. DB connection succeeds without exposed credentials.
7. zMovie readiness returns ready.
8. WordPress REST returns expected JSON.
9. Creator entitlement is verified end-to-end.
10. Sandbox Commerce and Ticketing remain isolated.
11. Nginx configuration passes syntax validation.
12. Cloudflare DNS and tunnel ingress remain healthy.
13. Backups and cron still work.
14. Unrelated production services remain unchanged.

Run service-specific restarts or reloads only when necessary.

Use staged configuration validation and rollback if a
service fails to recover.

Do not restart MariaDB, Cloudflared or unrelated services
merely because one environment file changed.

========================================================
PHASE 10 — SOURCE CONTROL AND RELEASE
========================================================

Do NOT commit:
  actual .env
  database credentials
  private signing keys
  license keys
  production certificates
  production databases
  Terraform state
  private backup archives

Commit:
  safe .env.example updates
  configuration validation scripts
  sanitized systemd templates
  infrastructure changes
  tests
  runbooks
  migration files
  security improvements

Use focused PRs and existing CI.

Do not push directly to a protected main branch or bypass
required checks.

Actual production .env changes remain local to the server
or managed through the approved secret-management system.

Record which runtime services were reloaded and verified.

========================================================
REQUIRED FINAL REPORT — THAI
========================================================

Provide a detailed Thai implementation report.

SECTION 1 — REAL ENVIRONMENT UPDATE

For every actual environment file, report:

  File path
  Service consuming it
  Modified: YES/NO
  Permission validation: PASS/FAIL
  Config validation: PASS/FAIL
  Runtime loading: PASS/FAIL
  Health check: PASS/FAIL
  Backup location: protected path only

List configured VARIABLE NAMES and whether they are set.

Never show their real values.

SECTION 2 — FEATURE COMPLETION

Report each remaining feature:

  feature
  actual implementation path
  status
  tests
  deployment evidence
  next blocker

SECTION 3 — SECURITY

Report:
  secret exposure scan
  HTTPS validation
  License Server E2E
  access-control tests
  migration integrity
  backup and restore

SECTION 4 — SOURCE CONTROL

Report:
  repository
  branch
  commit SHA
  PR URL
  CI result

SECTION 5 — REMAINING GATES

Classify every gate:

  VERIFIED
  IMPLEMENTED_NOT_VERIFIED
  BLOCKED
  NOT_APPLICABLE

Keep these disabled until separately approved:

  real payment capture
  live ticket sales
  public automatic publication

If any essential existing secret or service is unavailable,
do not invent credentials or use placeholder values.
Complete independent work and report the precise blocker.

START NOW.

Your first actual deliverable must be a verified update of
the REAL runtime environment on this machine, followed by
successful WordPress-to-License-Server HTTPS activation.

Continue into all remaining safe feature and production
readiness phases without stopping at documentation.