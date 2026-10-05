# ZMOVIE MASTER PROMPT
# NEXT PHASE — PRODUCTION RESILIENCE & ENTERPRISE RELEASE
# Date: 2026-09-25
# Execution mode: Autonomous, phase-gated, evidence-driven

ROLE

You are OpenCode acting as:

- Principal Platform Architect
- Senior Linux / SRE Engineer
- Cloudflare and Terraform Engineer
- Security Engineer
- Python / FastAPI Engineer
- WordPress Engineer
- PostgreSQL Engineer
- QA and Release Engineer

Your mission is to complete the remaining enterprise production-readiness
requirements for zMovie and ZeaZ Cinema while preserving the currently
operational production environment.

Implement changes directly wherever safe and authorized.
Do not stop after generating another plan.

LANGUAGE

All explanations, progress reports, documentation and final reports
must be written in Thai.

All code, CLI commands, configuration files, Terraform, Python, PHP,
YAML, JSON and environment variable names must remain in English.

Follow AGENTS.md in every relevant repository.

=================================================================
1. PROJECTS AND CURRENT BASELINE
=================================================================

Main application:

  ~/zmovie
  https://github.com/cvsz/zmovie

Cloudflare infrastructure:

  ~/platforms/zworkforce
  https://github.com/cvsz/zworkforce

Terraform:

  ~/platforms/zworkforce/infrastructure/terraform/cloudflare

Production:

  https://zmovie.zeaz.dev/
  https://zmovie.zeaz.dev/cinema/
  https://license.zeaz.dev

Reported zMovie commit:

  329d821

Reported infrastructure working branch:

  fix/security-production-secrets

Fetch remote refs and verify their current SHAs before making changes.

Do not use historical commit identifiers as immutable deployment targets.

=================================================================
2. COMPLETED WORK — DO NOT REIMPLEMENT
=================================================================

The operator's latest report states that the following were verified:

- Production environment inventory and file permissions
- /etc/zmovie/zmovie.env
- /etc/zmovie/zmovie-staging.env
- WordPress PHP-FPM secret delivery
- Ed25519 License Server integration
- Real WordPress license activation
- License E2E: 12/12
- Python unit tests: 178 passed, 2 PostgreSQL tests skipped
- Separate application staging environment
- WordPress and License HTTPS
- Existing backups and scheduled jobs
- Existing restore and rollback evidence
- Disk-pressure monitoring
- Cloudflare DNS and tunnel read-only verification

Read the existing evidence files before repeating any completed task.

Preserve all valid credentials, deployment settings and active
services unless a verified security defect requires changes.

Do not recreate the License Server.

Existing source:

  services/license-server/

=================================================================
3. GLOBAL SAFETY RULES
=================================================================

Never:

- Print or commit passwords, tokens or private keys
- Extract credentials from process command lines
- Force-unlock Terraform
- Delete Terraform state
- Force-push Git history
- Use git reset --hard on user work
- Kill the currently healthy Cloudflare connector prematurely
- Restart unrelated production services unnecessarily
- Run destructive database migrations without approval
- Enable live payments without authorization
- Enable live ticket sales without authorization
- Auto-publish content without verified distribution rights

Preserve working production traffic throughout infrastructure changes.

Use feature branches and focused PRs for new code.

Record exact commands, timestamps, commit SHAs, tests and actual results.

If a step is blocked, complete every other independent, safe task.

=================================================================
PHASE 0 — REFRESH BASELINE
=================================================================

Inspect the actual machine and repositories.

Check:

  git status --short
  git branch --show-current
  git rev-parse HEAD
  git fetch origin
  git log -5 --oneline

Inspect:

  systemctl status
  ss -tlnp
  nginx -t
  cloudflared version
  installed Terraform version
  running database services
  active deployment configuration

Inspect actual runtime environment paths without revealing values.

Verify:

  Production zMovie process
  Staging process
  WordPress PHP-FPM
  License API
  MySQL
  Nginx
  Cloudflare connector
  Backup jobs
  Disk monitoring

Classify findings as:

  VERIFIED
  IMPLEMENTED_NOT_VERIFIED
  DEFECTIVE
  BLOCKED

Create a new timestamped evidence directory outside Git.

=================================================================
PHASE 1 — P0: CLOUDFLARED ZERO-DOWNTIME RECOVERY
=================================================================

CURRENT RISK:

The operator reports:

  core-cloudflared.service: crash-looping
  healthy tunnel traffic: manual cloudflared process

The manual process reportedly exposes its tunnel token in
its command-line arguments.

This is a high-priority availability and credential-exposure risk.

GOAL:

Move Cloudflare Tunnel ownership to a reliable, secured
systemd service without interrupting existing production traffic.

STEP 1 — READ-ONLY DISCOVERY

Identify:

  current connector version
  existing tunnel identity
  active connector count
  current systemd unit
  service user
  restart configuration
  tunnel configuration
  current ingress routes
  credential source
  connector health

Determine the installed cloudflared version and supported secure
credential-delivery mechanisms.

Do not copy the token from /proc or process arguments.

Obtain authorized credentials through the existing secret manager
or another operator-approved secure recovery mechanism.

STEP 2 — SECURE CREDENTIAL DELIVERY

Choose a supported mechanism such as a protected tunnel
credential file or systemd credential facility.

Requirements:

  restrictive file permissions
  dedicated service identity where compatible
  no literal token in ExecStart
  no token in environment diagnostics
  no token in Git
  no token in process command arguments
  no token in application logs

Validate the actual supported cloudflared invocation
before changing the service.

Do not invent unsupported token-file arguments.

STEP 3 — PARALLEL CONNECTOR VALIDATION

If the existing tunnel and Cloudflare account support multiple
simultaneous connectors, start the managed connector in parallel.

Keep the working manual connector running.

Verify:

  Managed connector is healthy
  Correct tunnel identity
  Correct hostname ingress
  WordPress route works
  zMovie root works
  License API works
  No unexpected redirect loops
  No increase in connection failures

Test:

  https://zmovie.zeaz.dev/
  https://zmovie.zeaz.dev/cinema/
  https://license.zeaz.dev

STEP 4 — CONTROLLED CUTOVER

Only after the managed connector passes all checks:

  Confirm new connector health and stability.
  Confirm systemd restart behavior.
  Verify expected tunnel connector registration.

Perform a controlled retirement of the manual process.

If the managed connector fails, retain or restore the
known-good connector immediately.

Do not revoke the old credential before confirming the
replacement is operational.

STEP 5 — REBOOT RESILIENCE

Do not reboot the production server without explicit approval.

Use systemd restart and isolated failure-injection tests where safe.

Verify:

  service enabled
  restart policy
  dependency ordering
  credential access
  network recovery
  connector health
  log rotation

Prepare an operator-approved reboot acceptance test.

DELIVERABLES:

  Secure systemd unit
  Redacted configuration template
  Deployment runbook
  Rollback runbook
  Service health evidence

P0 GATE:

  Managed connector healthy
  No token in process arguments
  All three public routes healthy
  Previous manual process safely retired
  Recovery procedure documented

=================================================================
PHASE 2 — TERRAFORM STATE LOCK AND INFRASTRUCTURE GOVERNANCE
=================================================================

CURRENT RISK:

A Terraform lock was reported as remaining from September 24.

Do not force-unlock it.

FIRST:

Determine:

  Terraform backend
  active lock identifier
  lock creation time
  lock owner
  whether another Terraform process remains active
  whether a prior plan/apply is still running
  whether CI or automation owns the lock

Inspect:

  current local branch
  origin/main
  fix/security-production-secrets
  existing infrastructure PRs
  Terraform state
  DNS and tunnel resources

Do not run concurrent Terraform operations against the same state.

If an active Terraform operation exists:

  Leave the lock intact.
  Record its owner and operation.
  Continue independent phases.

If the lock appears stale:

  Collect evidence.
  Identify the authorized owner.
  Prepare a documented recovery procedure.
  Obtain explicit approval before unlocking.

Never remove lock files or database lock records manually.

AFTER LOCK RESOLUTION:

Run:

  terraform fmt -check -recursive
  terraform validate
  terraform plan

Verify:

  cloudflare_dns_record.zmovie
  license hostname record
  tunnel ingress
  existing unrelated services
  zero unexpected destruction

Reconcile the working infrastructure branch with main through
a focused PR when appropriate.

Do not duplicate resources already present in state.

Do not apply a plan containing unexpected production changes.

DELIVERABLE:

  Terraform state reconciliation report
  Reviewed plan summary
  Infrastructure PR
  Import/recovery evidence if applicable

=================================================================
PHASE 3 — LOCAL POSTGRESQL INTEGRATION
=================================================================

CURRENT GAP:

Two PostgreSQL tests were skipped because ZMOVIE_PG_DSN
was not configured.

The current production database arrangement must remain unchanged.

Do not migrate production data during this phase.

FIRST:

Inspect the real PostgreSQL requirements in:

  services/cinema-api/
  Commerce modules
  Ticketing modules
  Existing migrations
  Existing test fixtures

Verify that the application and migrations genuinely support
PostgreSQL rather than merely containing a portable-looking schema.

CREATE AN ISOLATED TEST DATABASE.

Use an approved local PostgreSQL service or disposable
PostgreSQL container.

Requirements:

  separate test database
  separate database user
  isolated credentials
  restricted network binding
  no production data
  no production credentials
  reproducible migrations

Configure ZMOVIE_PG_DSN only in the isolated test environment.

RUN:

  existing PostgreSQL integration tests
  migrations
  transaction rollback tests
  concurrency tests
  backup and restore checks

TICKETING INVARIANTS:

  A seat cannot be sold twice.
  Expired holds cannot generate valid purchases.
  Duplicate requests cannot issue duplicate tickets.
  Concurrent booking operations remain consistent.
  Failed transactions release resources correctly.

Use actual concurrent database connections.

Test across multiple application workers where applicable.

Do not rely on SQLite passing as evidence of PostgreSQL
transactional correctness.

DELIVERABLE:

  PostgreSQL integration configuration
  Test fixtures
  Migration evidence
  Concurrency test evidence
  Database backup/restore runbook

Do not switch the production database without a separate
reviewed migration and explicit operator approval.

=================================================================
PHASE 4 — COMPLETE CI AND SECURITY TOOLCHAIN
=================================================================

CURRENT GAP:

Ruff installation previously failed because of network stalls.

Full SBOM, image scanning and Continuous Deployment evidence
remain incomplete.

FIRST:

Inspect existing dependency lock files, cache and CI workflows.

Do not modify application requirements merely because a
package download failed.

Use approved package sources and verified package integrity.

Complete:

  Ruff
  Pytest
  PHP lint
  JavaScript checks
  ShellCheck
  Docker Compose validation
  Dependency auditing
  Secret scanning
  SBOM generation
  Container vulnerability scanning

Use maintained tools compatible with the existing project.

Create reproducible toolchain installation instructions.

Add the missing CI jobs as independently reviewable changes.

SECURITY GATES:

  No committed secrets
  No unauthorized private keys
  No unexpected vulnerable production dependencies
  No critical image vulnerabilities without documented exception
  SBOM generated for release artifacts
  Build provenance recorded
  CI artifacts retained according to project policy

Do not suppress failing scanners to obtain green checks.

If a vulnerability has no available fix, document:

  affected package
  installed version
  advisory
  actual exposure
  mitigation
  owner
  deadline

DELIVERABLE:

  CI workflow updates
  Security evidence
  SBOM artifacts
  Reproducible toolchain instructions

=================================================================
PHASE 5 — FULL AUTHENTICATED END-TO-END ACCEPTANCE
=================================================================

Current public browser smoke tests are insufficient to verify
all authenticated operations.

Use the existing isolated staging environment.

Create disposable test users and test data.

TEST ROLES:

  Anonymous viewer
  Registered viewer
  Licensed creator
  Cinema administrator

EXECUTE:

Anonymous:

  Browse the cinema
  Search and filter films
  Play an authorized trailer
  Reject unauthorized favorites mutation
  Reject creator-only operations

Registered viewer:

  Login
  Favorite/unfavorite
  View saved films
  Account privacy export
  Account deletion confirmation
  Logout
  Expired-session handling

Licensed creator:

  Valid Ed25519 entitlement
  Submit authorized media
  Rights confirmation
  Pending editorial review
  View submission state
  Reject invalid or expired entitlement

Administrator:

  Review submission
  Approve or reject
  Publish authorized content
  Remove unauthorized content
  Audit the publication event

NEGATIVE TESTS:

  Wrong site
  Wrong audience
  Revoked test license
  Forged signature
  Missing nonce
  Invalid session
  Unauthorized object access
  Expired session
  Duplicate submission
  Oversized payload

Do not revoke the production license during testing.

Use isolated staging credentials and synthetic content.

BROWSER MATRIX:

  Desktop Chromium
  Mobile viewport
  Keyboard-only navigation
  Reduced-motion preference

Record screenshots only for successfully executed flows.

Redact all credentials and personal data.

=================================================================
PHASE 6 — MEDIA PIPELINE AND PERFORMANCE
=================================================================

Inspect the existing media-processing features and
A11Y_PERF_EVIDENCE.md before adding new implementation.

Do not reimplement completed work.

Validate:

  Authorized uploads
  File-size restrictions
  MIME validation
  Media probing
  FFmpeg processing
  Poster generation
  Thumbnail generation
  Worker retries
  Processing failures
  Queue recovery
  Storage quotas
  Rights enforcement
  Editorial approval

If real model weights or accelerated hardware are unavailable:

  Complete deterministic non-model tests.
  Preserve existing CPU fallback.
  Mark accelerated real-model evidence BLOCKED.
  Do not invent model-output evidence.

PERFORMANCE:

Measure in isolated staging:

  API latency
  License activation latency
  Media-processing throughput
  Database transaction latency
  Booking concurrency
  Frontend responsiveness
  Queue recovery

Use reproducible load-test parameters.

Do not run disruptive load tests against the production site.

Propose SLOs for operator approval based on actual measurements.

=================================================================
PHASE 7 — ACCESSIBILITY AND PRIVACY ACCEPTANCE
=================================================================

Review existing accessibility evidence before rerunning tools.

Complete outstanding checks using automated testing
and targeted manual review.

Target WCAG 2.2 AA-oriented acceptance.

Verify:

  Keyboard navigation
  Visible focus
  Screen-reader controls
  Form labels and errors
  Video captions where required
  Reduced motion
  Sufficient contrast
  Responsive layouts
  Touch targets
  Accessible authentication flows

Correct confirmed defects.

For privacy, validate:

  Account data export
  Account deletion
  Authentication and reauthentication
  Data ownership checks
  PII redaction
  Audit-log minimization
  Retention
  Authorized backup handling

Do not include real customer data in automated fixtures.

Do not claim full WCAG conformance without sufficient
automated and manual audit evidence.

=================================================================
PHASE 8 — RELEASE AUTOMATION
=================================================================

Create or improve the existing release pipeline.

Desired flow:

  Approved Git commit
       |
  Tests and security scans
       |
  Build immutable artifacts
       |
  SBOM and provenance
       |
  Deploy to staging
       |
  Migration verification
       |
  Authenticated smoke tests
       |
  Operator approval
       |
  Production promotion
       |
  Health checks
       |
  Rollback if required

Do not deploy arbitrary feature-branch code directly
to production.

Required safeguards:

  Branch protection
  Required CI
  Deployment environment permissions
  Immutable build reference
  Minimal deployment credentials
  Predeployment backup
  Migration compatibility check
  Health/readiness probes
  Documented rollback

Do not enable unrestricted auto-update of custom
WordPress plugins or themes.

Preserve the existing WordPress and zMovie deployment
architecture unless a change is justified.

=================================================================
PHASE 9 — SECURITY AND AVAILABILITY HARDENING
=================================================================

Reevaluate the reported:

  ZMOVIE_HOST=0.0.0.0

The existing UFW configuration currently restricts exposure.

Do not restart production merely to change this value.

Add defense-in-depth when a safe maintenance window is available.

Prefer loopback binding when the application is accessed
only through a local reverse proxy.

Validate Nginx upstream connectivity before changing the binding.

Review:

  Firewall exposure
  Reverse-proxy trust boundaries
  Cloudflare Tunnel access
  Administrative API exposure
  Authentication
  Session handling
  Rate limiting
  MySQL privileges
  Secrets ownership
  Log retention
  Backup permissions

Verify license-admin endpoints are protected both
at the network edge and within the application.

No public endpoint may return secrets or private diagnostics.

=================================================================
PHASE 10 — RECOVERY AND OPERATIONS
=================================================================

Preserve the existing daily backup and weekly recovery jobs.

Do not create duplicate schedules.

Expand recovery coverage to include:

  zMovie production
  zMovie staging
  WordPress
  License Server
  Commerce data
  Ticketing data
  Media assets
  Signing-key recovery procedures
  Cloudflare configuration

Store key material through an independently secured backup
mechanism.

Do not place unencrypted private keys in general backup archives.

Run an isolated restore for every supported durable database.

Validate restored data and service startup.

Measure actual RPO/RTO rather than inventing targets.

Document how to recover after:

  Host reboot
  Cloudflare connector failure
  Database corruption
  Lost application container
  Invalid deployment
  Signing-key compromise
  Expired or unavailable TLS certificate

Set up actionable monitoring and alerting.

=================================================================
PHASE 11 — FINAL PRODUCTION ACCEPTANCE
=================================================================

Recheck all major routes:

  https://zmovie.zeaz.dev/
  https://zmovie.zeaz.dev/cinema/
  https://license.zeaz.dev

Verify:

  Real TLS
  Correct redirects
  Correct application routing
  WordPress REST API
  License activation
  Admin access restrictions
  Session handling
  Worker health
  Backup health
  Cloudflare connector health

Repeat relevant tests after each deployment.

Do not enable:

  live payment capture
  live ticket sales
  public automatic publication

These require separate operational, security, payment
and legal acceptance.

=================================================================
SOURCE CONTROL
=================================================================

Use separate, focused branches for zMovie and zWorkforce.

Example branches:

  fix/cloudflared-managed-service
  fix/terraform-state-reconciliation
  test/postgres-integration
  ci/release-security-evidence
  test/cinema-authenticated-e2e
  ops/release-automation

Use conventional commits.

Keep unrelated changes out of each PR.

Run applicable tests and CI before merging.

Never bypass required checks.

Do not claim a PR was merged unless GitHub confirms it.

=================================================================
FINAL DELIVERABLES
=================================================================

Update existing documentation instead of creating
duplicate conflicting reports.

Expected documentation:

  docs/production/CURRENT_STATE.md
  docs/production/FEATURE_MATRIX.md
  docs/production/TEST_EVIDENCE.md
  docs/production/FINAL_READINESS_REPORT.md
  docs/production/DEPLOYMENT_RUNBOOK.md
  docs/production/BACKUP_RESTORE_EVIDENCE.md
  docs/production/ROLLBACK_EVIDENCE.md
  docs/production/A11Y_PERF_EVIDENCE.md

Add focused runbooks for:

  Cloudflared managed-service recovery
  Terraform lock recovery
  Signing-key rotation
  PostgreSQL migration
  Release promotion
  Incident response

Avoid duplicating documents that already exist.

=================================================================
FINAL THAI REPORT
=================================================================

Report the following:

1. Actual repository baseline and changes.

2. Cloudflared recovery:
   - original problem
   - secure credential delivery
   - managed connector health
   - zero-downtime transition evidence
   - reboot recovery status

3. Terraform:
   - lock ownership
   - resolution status
   - plan result
   - drift
   - infrastructure PR

4. PostgreSQL:
   - isolated test database
   - migrations
   - integration tests
   - booking concurrency
   - production migration blockers

5. CI and security:
   - Ruff
   - Unit tests
   - Secret scanning
   - SBOM
   - Image scanning
   - Release pipeline

6. Full authenticated E2E results.

7. Accessibility and performance evidence.

8. Backup/restore and rollback results.

9. Commit SHAs, PR URLs and CI results.

10. Remaining P0/P1/P2 issues.

For each production gate use:

  VERIFIED
  IMPLEMENTED_NOT_VERIFIED
  BLOCKED
  NOT_APPLICABLE

Do not hide skipped tests or unavailable dependencies.

Do not report Full Production Readiness unless
all applicable P0/P1 acceptance criteria have real evidence.

EXECUTION ORDER:

1. Reconcile the actual environment.
2. Secure and stabilize Cloudflared.
3. Inspect Terraform lock without force-unlocking.
4. Complete independent PostgreSQL testing.
5. Finish CI and security toolchain.
6. Execute authenticated staging E2E.
7. Complete remaining accessibility and performance tests.
8. Implement release automation.
9. Perform recovery verification.
10. Update the final production evidence.

START NOW.

Implement all safe, independent changes.
Stop before unapproved destructive or irreversible operations.
