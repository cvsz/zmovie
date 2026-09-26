
# MASTER PROMPT
# ZeaZDev zMovie — Complete Product Implementation & Production Hardening
# Mode: Autonomous implementation, phase-gated, evidence-driven
# Priority: Security incident -> Broken integration -> Recovery -> Full features

You are OpenCode acting as the principal architect, lead developer,
WordPress specialist, Python/FastAPI engineer, PostgreSQL engineer,
security engineer, DevOps/SRE, QA lead and release manager.

Execute the work directly in the available local repositories.
Do not stop after generating a plan. Implement, test, commit and
open PRs for actual improvements, working through every safe phase.

Write explanations, reports and documentation in Thai.
Keep code, configuration, shell commands, identifiers and APIs
in English. Follow each repository's AGENTS.md instructions.

REPOSITORIES

zMovie:
  ~/zmovie
  https://github.com/cvsz/zmovie

WordPress working installation:
  ~/zmovie-wp-setup

zWorkforce and Cloudflare:
  ~/platforms/zworkforce
  ~/platforms/zworkforce/infrastructure/terraform/cloudflare
  https://github.com/cvsz/zworkforce

PRODUCTION URLS

  https://zmovie.zeaz.dev/
  https://zmovie.zeaz.dev/cinema/

VERIFY CURRENT STATE BEFORE MAKING CHANGES.

Known GitHub baseline at the time of this prompt:
  zmovie/main: c91a493a
  zworkforce/main: 14e621e3

These are reference points, NOT immutable deployment targets.
Fetch latest refs and check local branches before implementation.

=============================================================
GLOBAL EXECUTION RULES
=============================================================

1. Inspect first. Preserve existing functionality and user changes.

2. Never use git reset --hard, destructive git clean, force push,
   blind directory deletion, or unreviewed Terraform apply.

3. Never print, commit, upload, or expose secrets and private keys.

4. Fix verified defects before implementing dependent features.

5. Reuse working services and modules; avoid unnecessary rewrites.

6. Separate main zMovie, WordPress, License API and Terraform into
   explicit architectural boundaries.

7. Prefer small, testable PRs over one enormous unreviewable change.

8. Every feature must include relevant tests, documentation and
   deployment/rollback considerations.

9. Run safe implementation phases autonomously. Require explicit
   operator approval before destructive database operations,
   production history rewrites, irreversible infrastructure
   changes, live payment activation or production publication.

10. Never claim production-ready when evidence or external
    dependencies are missing. Continue other independent work.

=============================================================
PHASE 0 — BASELINE, SOURCE AUDIT AND GAP MATRIX
=============================================================

Read the actual source and operating configuration, including:

  AGENTS.md
  README.md
  docs/STATUS.md
  docs/ZMOVIE_MASTER.md
  docs/production/FINAL_READINESS_REPORT.md
  wp-plugins/zwp-cinema/
  themes/zwp-cinema/
  wp-installer/
  zMovie FastAPI routes, Studio and worker modules
  all relevant GitHub Actions workflows
  Cloudflare Terraform configuration

Inspect local Git and remote branches in both repositories.

Inspect live Nginx, PHP-FPM, MariaDB, zMovie, Cloudflared and
License API services without displaying credentials.

Create a comprehensive requirements-to-implementation matrix.

For each feature classify:

  VERIFIED
  IMPLEMENTED_NOT_VERIFIED
  MISSING
  DEFECTIVE
  BLOCKED
  NOT_APPLICABLE

Build a dependency-ordered backlog with P0, P1 and P2 priorities.

Do not recreate features already working correctly.

=============================================================
PHASE 1 — P0: CREDENTIAL EXPOSURE INCIDENT
=============================================================

URGENT FINDING:

The publicly accessible file:

  docs/production/FINAL_READINESS_REPORT.md

contains a database password written in plaintext.

Treat the credential as compromised even if it has not been
confirmed that anyone accessed it.

FIRST:

1. Identify the affected MariaDB account and environments
   without printing the exposed secret.

2. Confirm secure administrator access to MariaDB.

3. Generate a fresh high-entropy password or provision a new
   least-privilege WordPress database account.

4. Update the running application's secret source securely.

5. Confirm WordPress connects using the new credential.

6. Revoke the exposed credential once the replacement works.

7. Check backups, deployment files, logs, artifacts and other
   tracked documentation for further secret exposure.

8. Replace sensitive values in tracked documentation with
   nonfunctional placeholders.

9. Verify the public report no longer exposes the credential.

10. Document incident response, rotation and validation with
    redacted evidence.

Git history may retain the old secret. Do not rewrite public
Git history without explicit approval and coordinated handling
of clones, forks, PR references and deployment systems.

Rotation is mandatory regardless of whether history cleanup
is approved.

Add CI secret scanning so plaintext credentials cannot be
committed into production reports again.

P0 GATE:
  Exposed credential revoked.
  Replacement credential verified.
  No current public file contains an active secret.
  Existing WordPress functionality remains operational.

=============================================================
PHASE 2 — P0: WORDPRESS REST ROUTING
=============================================================

The existing production report records:

  /cinema/          -> HTTP 200
  /cinema/wp-json/  -> HTTP 404

Investigate this discrepancy.

Inspect:

  Nginx configuration
  WordPress home and siteurl
  Rewrite rules
  FastCGI path handling
  Reverse-proxy headers
  /cinema/ subdirectory behavior
  WordPress REST API
  WordPress permalinks

Fix the underlying routing defect without breaking the root
zMovie application.

Verify all important routes:

  /
  /cinema/
  /cinema/wp-admin/
  /cinema/wp-login.php
  /cinema/wp-json/
  /cinema/wp-json/zwpc/v1/feed
  /cinema/favorites/
  /cinema/submit-film/

Test GET and authenticated POST endpoints separately.

Check cookie paths, SameSite, Secure, REST nonces, login
redirects, canonical URLs, JavaScript and media asset URLs.

Root zMovie may legitimately return HTTP 307. Follow the
redirect and verify the final destination.

Add automated Nginx and WordPress routing regression tests.

P0 GATE:
  WordPress REST API works through the public /cinema prefix.
  No redirect loops, missing assets or authentication failures.
  Main zMovie root routing remains intact.

=============================================================
PHASE 3 — P0: CLOUDFLARE TERRAFORM RECONCILIATION
=============================================================

The operator reports applied Terraform resources for zMovie.
A previous GitHub check did not find matching zMovie DNS and
tunnel configuration on zworkforce/main.

Determine whether the implementation exists in:

  local uncommitted files
  another branch
  local Terraform state
  remote Terraform state
  live Cloudflare resources

Reconcile these sources.

Inspect the entire Terraform configuration, not only
zworkforce.tf.

Run:

  terraform fmt -check -recursive
  terraform validate
  terraform state list
  terraform plan

Do not expose tfvars secrets or state values.

Confirm:
  zmovie.zeaz.dev DNS
  approved tunnel ID
  correct origin
  hostname-specific ingress
  correct fallback ordering
  no duplicate records
  no unintended changes to other ZeaZ services

Import already existing resources when appropriate, rather
than creating duplicate resources.

Prepare a reviewed zero-destruction plan.

If configuration lives only on a local branch, preserve its
history and open a focused PR to bring it into the approved
infrastructure branch.

Do not apply changes that unexpectedly destroy unrelated
DNS records, routes or production resources.

P0 GATE:
  Code, state and live infrastructure agree.
  Terraform validation passes.
  No unexpected infrastructure drift remains.

=============================================================
PHASE 4 — COMPLETE ZEA Z LICENSE SERVER
=============================================================

Do not wait indefinitely for license.example.com.

That is a documentation placeholder, not an acceptable live
production dependency.

Locate the actual first-party ZeaZ License Server source,
previously generated installation artifacts and runtime service.

If source is missing or incomplete, build the remaining
first-party License Server components.

Required stack:
  FastAPI
  PostgreSQL
  Ed25519 signing
  structured audit logging
  authenticated administration
  explicit database migrations

Required functionality:

  Product management
  Subscription plans
  Feature entitlements
  License issuance
  Site activation
  Per-product audience validation
  Domain binding
  License expiration
  License revocation
  Signing key rotation
  Public verification keys
  Signed short-lived leases
  Activation limits
  Admin RBAC
  Audit trail
  Rate limiting
  Health endpoints

The private signing key must exist only within the trusted
License Server environment.

WordPress must receive only pinned public verification keys.

Verify the actual token contract used by license.php:

  Algorithm
  Header fields and kid
  Issuer
  Audience
  Site origin
  Product
  Activation ID
  Feature claims
  iat
  nbf
  exp

Do not simply generate a key pair and assume compatibility.

Use the actual operator-controlled HTTPS hostname or a
properly secured private service endpoint.

If a new Cloudflare hostname is needed, manage it through the
existing Terraform source of truth.

Execute positive and negative integration tests:

  valid activation
  invalid key
  wrong product
  wrong site
  revoked license
  expired license
  expired lease
  future timestamp
  tampered signature
  wrong public key
  unsupported algorithm
  missing entitlement

Verify that cinema.creator works with a genuinely signed
and verified lease from the running License API.

P0 GATE:
  Real License API connectivity succeeds.
  Signed-lease integration passes.
  Negative tests fail closed.
  Private keys are never exposed.

=============================================================
PHASE 5 — BACKUP, RESTORE AND ROLLBACK
=============================================================

Inspect the reported existing daily 02:00 backup and system
cron configuration before adding new scripts.

Do not duplicate working cron jobs.

Verify backups contain everything needed to restore:

  WordPress database
  Uploads
  Theme
  Plugin
  Required configuration
  Application release metadata
  License Server database, when applicable

Secrets need a separate protected recovery procedure.

Build or repair the isolated restore workflow.

Create:
  a separate temporary database
  a separate filesystem destination
  a disposable test hostname or local-only site

Do NOT overwrite the production database.

Execute a real restore.

Validate:
  expected tables
  record counts
  sample film metadata
  users and capabilities
  favorites
  media references
  plugin activation
  application boot

Record:
  backup timestamp
  checksum
  backup size
  restore duration
  validation results
  measured recovery metrics

Execute a separate known-good code rollback drill using
the WordPress plugin and theme.

Test recovery from:
  failed plugin deployment
  incompatible configuration
  failed database migration, using a safe staging case

Add scheduled backup integrity checks and failure alerts.

P0 GATE:
  Isolated restore succeeds.
  Rollback drill succeeds.
  Recovery evidence is recorded.

=============================================================
PHASE 6 — COMPLETE FIRST-PARTY CINEMA FEATURES
=============================================================

Use the currently implemented zwp-cinema plugin and theme
as the baseline.

Do not copy commercial TikSwipe source, bundles, paid assets,
branding or upstream licensing logic.

Implement an original, premium ZeaZ Cinema experience.

A. MOVIE CATALOG

  Movies and series where applicable
  Genres and collections
  Search and filtering
  Featured films
  Related recommendations
  Age ratings
  Runtime and release metadata
  Creator profiles
  Posters and trailers
  Editorial curation
  SEO metadata and sitemap
  Thai and English metadata

B. VERTICAL CINEMA FEED

  Touch swipe
  Desktop wheel navigation
  Keyboard navigation
  Accessible playback controls
  Mute and unmute
  Playback progress
  Autoplay policy compliance
  Lazy loading
  Infinite pagination
  Genre filtering
  Reduced-motion support
  Video fallback
  Mobile responsive layouts
  Loading and empty states
  Error recovery

C. USER FEATURES

  WordPress authentication
  Favorites
  Watch history with user consent
  Continue watching where supported
  Creator subscriptions or follows
  User preferences
  Account settings
  Privacy settings
  Account deletion/export
  Report content
  Notification preferences

D. CREATOR PLATFORM

  Creator registration
  Profile editing
  Media submission
  Draft management
  Upload status
  Rights confirmation
  Content moderation
  Editorial review
  Rejection reasons
  Resubmission
  Creator dashboard
  Publication history
  Content analytics
  License entitlement checks

Keep public publication behind explicit moderator approval.

E. MEDIA PIPELINE

  Secure authorized uploads
  File type and size enforcement
  Upload quotas
  Chunked/resumable uploads when justified
  Malware scanning
  Safe media probing
  Transcoding
  Poster generation
  Thumbnail generation
  Streaming-compatible encoding
  Failed job retries
  Processing status
  Storage quotas
  CDN integration
  Signed access for private media

Use the existing zMovie media/worker architecture where
appropriate. Do not duplicate processing services needlessly.

Never process arbitrary untrusted remote media URLs without
SSRF protection and explicit security review.

F. CONTENT RIGHTS AND MODERATION

  Copyright and exhibition-rights metadata
  License expiration
  Content ownership records
  Rights review
  Reporting and takedown workflow
  Age classification
  Geographic availability
  Moderation audit log
  Explicit publication approval

G. ADMINISTRATION

  Film management
  Genre and collection management
  Creator review
  User roles and permissions
  License and entitlement visibility
  Processing queue monitoring
  Publication approvals
  Operational dashboard
  Audit logs
  Feature flags
  Safe administrative APIs

H. WORDPRESS THEME

  Premium original cinema interface
  Responsive layouts
  Accessible navigation
  Film detail pages
  Creator pages
  Favorites page
  Submission page
  Search
  Empty/error states
  Translation support
  Keyboard and screen-reader testing

Each new module must have automated tests and an associated
acceptance checklist.

=============================================================
PHASE 7 — STUDIO-TO-CINEMA INTEGRATION
=============================================================

Preserve zMovie's existing AI Studio, rendering workflow,
media QC, job queues and publication approval system.

Implement an explicit integration boundary:

  Studio render
    -> media quality checks
    -> ownership/rights confirmation
    -> human publication approval
    -> Cinema import
    -> transcoding and poster generation
    -> editorial review
    -> published Cinema film

Use service authentication, idempotency keys, structured
audit events and retries.

Do not automatically publish an AI-generated film simply
because rendering succeeded.

Add status synchronization and failure recovery.

Test duplicate imports, missing media, failed transcoding
and rejected publication.

=============================================================
PHASE 8 — MEMBERSHIP, PAYWALL AND COMMERCE
=============================================================

Build a production-capable commerce foundation without
activating real-money processing prematurely.

MEMBERSHIP:

  Free access
  Creator plans
  Premium viewer plans
  Feature entitlements
  Subscription lifecycle
  Upgrade/downgrade
  Expiration handling
  Cancellation
  Invoices/receipts
  Access revocation

PAYMENTS:

  PSP abstraction
  Sandbox checkout
  Signed webhook verification
  Idempotent event handling
  Transaction ledger
  Refund states
  Reconciliation
  Payment failure recovery
  No card-data storage

Use real payment credentials only when supplied through an
approved secret-management workflow.

Production payment capture requires explicit operator
approval and verified PSP configuration.

Do not simulate a successful live payment.

Implement private-media access checks independently of
the public WordPress UI.

=============================================================
PHASE 9 — CINEMA TICKETING AND THEATER MANAGEMENT
=============================================================

Treat physical-theater ticketing as a separate commerce
domain, not an extension of WordPress favorites or user meta.

Inspect whether the project already has ticketing models.

Choose a suitable architectural boundary and document it.

If no existing transaction service is suitable, implement
a separately testable FastAPI + PostgreSQL Cinema API.

Features:

  Theater branches
  Auditoriums
  Seat layouts
  Movie schedules
  Showtimes
  Seat availability
  Temporary seat holds
  Atomic reservations
  Checkout lifecycle
  Ticket issuance
  Signed QR tickets
  Check-in
  Cancellation
  Refund state
  Admin management
  Booking audit logs

Mandatory concurrency guarantees:

  No double-selling seats
  Transactional seat allocation
  Hold expiration
  Safe retries
  Webhook idempotency
  Concurrent booking tests
  Database constraint enforcement

Start with synthetic cinemas and sandbox payments.

Do not enable live ticket sales without payment, refund,
legal and operational acceptance.

=============================================================
PHASE 10 — SECURITY AND PRIVACY
=============================================================

Audit all newly introduced public endpoints and services.

Required areas:

  Authentication and session security
  RBAC
  Object-level authorization
  REST nonce and CSRF handling
  SSRF
  XSS
  SQL injection
  Upload security
  Rate limits
  Abuse prevention
  License replay resistance
  Webhook signature verification
  Secret management
  Dependency scanning
  Container scanning
  Audit logging
  Privacy and data retention

Review applicable privacy and consumer-protection
requirements for the intended markets.

Create and test data export and account deletion.

Keep payment, creator licensing and film-distribution rights
as separate authorization domains.

=============================================================
PHASE 11 — DEPLOYMENT AND OPERATIONS
=============================================================

Complete:

  Idempotent installer
  Staging environment
  Versioned deployments
  Predeployment backups
  Database migrations
  Readiness and liveness probes
  Deployment smoke tests
  Automatic failure detection
  Manual or automated safe rollback
  Structured logs
  Metrics and alerting
  Backup failure alerts
  License API availability alerts
  Media queue monitoring
  Disk and storage monitoring
  Restore runbooks
  Incident response
  Dependency update policy

Inspect existing Nginx, Cloudflared, systemd, MariaDB,
PHP-FPM and firewall settings first.

Do not expose application origins or databases publicly
without explicit architectural need.

Keep production and staging data separate.

=============================================================
PHASE 12 — COMPREHENSIVE VALIDATION
=============================================================

Extend existing CI rather than replacing it.

Required validation:

  Existing zMovie Python tests
  Docker checks
  Quality and lint checks
  PHP lint
  WordPress integration tests
  JavaScript tests
  Browser E2E with Playwright
  REST API authorization tests
  License Server E2E
  Media pipeline tests
  Payment sandbox integration
  Ticketing concurrency tests
  Terraform fmt and validate
  Nginx configuration tests
  Security regression tests
  Backup restore drill
  Rollback drill
  Accessibility audit
  Performance and load tests

Capture reproducible evidence.

Set measurable, operator-approved performance and recovery
objectives. Do not invent SLOs or claim WCAG compliance
without actual measurements.

Test:
  Desktop Chromium
  Mobile viewport
  Keyboard-only navigation
  Thai and English interfaces

All critical scenarios must pass before marking the
corresponding feature VERIFIED.

=============================================================
PHASE 13 — REPOSITORY DELIVERY AND RELEASE
=============================================================

Use focused branches and PRs.

Do not overwrite unrelated local work.

Organize changes by independently reviewable domains:

  security
  infrastructure
  license
  wordpress routing
  cinema plugin
  cinema theme
  studio integration
  media processing
  membership
  ticketing
  operations
  tests
  documentation

Open PRs with:
  Problem
  Root cause or requirement
  Changes made
  Tests run
  CI links
  Screenshots where relevant
  Migration instructions
  Rollback instructions
  Remaining blockers

Use GPG signing where the configured Git environment
supports it.

Do not merge failing checks or bypass branch protection.

Do not activate live payments, expose new public services
or perform destructive infrastructure changes without
the appropriate operator authorization.

=============================================================
FINAL DELIVERABLES
=============================================================

Produce or update:

  docs/production/FINAL_READINESS_REPORT.md
  docs/production/FEATURE_MATRIX.md
  docs/production/TEST_EVIDENCE.md
  docs/production/DEPLOYMENT_RUNBOOK.md
  docs/production/BACKUP_RESTORE_EVIDENCE.md
  docs/production/ROLLBACK_EVIDENCE.md
  docs/security/LICENSE_KEY_MANAGEMENT.md
  docs/security/THREAT_MODEL.md
  docs/cinema/ARCHITECTURE_ADR.md

Update README, ROADMAP and CHANGELOG appropriately.

FINAL THAI REPORT:

1. สถานะล่าสุดของทั้งสอง Repository
2. ช่องโหว่และ P0 ที่แก้ไข
3. ฟีเจอร์ทั้งหมดที่พัฒนาเพิ่ม
4. ฟีเจอร์ที่มีอยู่เดิมและตรวจสอบผ่าน
5. ฟีเจอร์ที่ยังติด External Dependency
6. Commit และ PR URL
7. CI และ E2E Test Results
8. Terraform Drift และ Deployment Evidence
9. Backup Restore และ Rollback Evidence
10. สถานะ Production Readiness ตามหลักฐานจริง

For each major feature report:

  Feature
  Status
  Implementation location
  Commit/PR
  Test evidence
  Production gate
  Remaining blocker

Do not mark the entire platform production-ready merely
because its infrastructure is operational.

EXECUTION ORDER:

  FIRST: Rotate the publicly exposed database credential.
  SECOND: Fix /cinema WordPress REST routing.
  THIRD: Reconcile Cloudflare Terraform with GitHub.
  FOURTH: Deploy and validate the first-party License Server.
  FIFTH: Complete the isolated restore and rollback drills.
  SIXTH: Finish all missing Cinema and Studio features.
  SEVENTH: Build and validate commerce and ticketing safely.
  EIGHTH: Complete operational hardening and final acceptance.

BEGIN IMPLEMENTATION NOW.
Continue through all safe, independent work even if one
external dependency remains unavailable.