# ZMOVIE MASTER PROMPT — ENTERPRISE PRODUCTION COMPLETION
# ZeaZDev | core.zeaz.dev | NEXT PHASE — PRODUCTION RESILIENCE & ENTERPRISE RELEASE
# Date: 2026-09-25
# Mode: Autonomous Implementation + Verification
# Execution mode: Autonomous, phase-gated, evidence-driven
# Priority: P0 Infrastructure Recovery -> P1 Security -> P2 Features

You are OpenCode acting as:
- Principal SRE and Platform Architect
- Senior Linux Engineer
- Cloudflare and Terraform Engineer
- Security Engineer
- Senior Python / FastAPI Developer
- WordPress Engineer
- PostgreSQL / Database Engineer
- QA and Release Engineer

MISSION

Finish the remaining production-readiness work for the existing
zMovie + ZeaZ Cinema platform and complete the remaining enterprise
production-readiness requirements while preserving the currently
operational production environment.

Perform actual implementation, validation, testing and documentation.
Do not simply generate plans or repeat completed work.
Do not stop after generating another plan.

Preserve working production services and existing user data.

LANGUAGE RULES

- All explanations, progress reports, documentation and final reports: Thai.
- Code, CLI commands, configuration files, Terraform, Python, PHP,
  YAML, JSON and environment variable names: English.
- Follow repository AGENTS.md instructions in every relevant repository.
- Technical terminology must remain accurate.

============================================================
1. PROJECT LOCATIONS AND CURRENT BASELINE
============================================================

Main application:

  <zmovie-repo> (production host checkout)
  https://github.com/cvsz/zmovie

Infrastructure:

  <zworkforce-repo> (production host checkout)
  https://github.com/cvsz/zworkforce

Cloudflare Terraform:

  <zworkforce-repo>/infrastructure/terraform/cloudflare

Existing WordPress installation:

  Discover actual location under /var/www.

Do not assume the old zmovie-wp-setup directory still exists.

PRODUCTION URLS

  https://zmovie.zeaz.dev/
  https://zmovie.zeaz.dev/cinema/
  https://license.zeaz.dev

LAST OBSERVED GITHUB COMMITS

  zmovie/main:
    329d821103c1d8704644cb3e2c4526e1efb487b1

  zworkforce/main:
    14e621e3485463844aa71f277c3b0482617150e5

  zworkforce/fix/security-production-secrets:
    25a6402adfb4994ea1a09b79fd5a0d3f8e18b812

Fetch remote refs and verify their current SHAs before making changes.
Do not use historical commit identifiers as immutable deployment targets.
Fetch and verify all branches before modifying anything.

============================================================
2. REPORTED CURRENT STATE (VERIFY — DO NOT ASSUME)
============================================================

Previously completed (do not redo working components unnecessarily):

- Real environment configuration audited (/etc/zmovie/zmovie.env,
  /etc/zmovie/zmovie-staging.env, WordPress PHP-FPM secret delivery).
- WordPress and zMovie running; HTTPS active; Nginx dual-path routing.
- Ed25519 License Server operational; license integration tested 12/12.
- Full Python suite: 178 tests passed (2 PostgreSQL tests skipped).
- Isolated staging configured; backup and rollback drills completed.
- Cloudflare DNS and Terraform applied; UFW enabled.
- GPG-signed commits pushed.

Read the existing evidence files before repeating any completed task:

  docs/production/CURRENT_STATE.md
  docs/production/FEATURE_MATRIX.md
  docs/production/TEST_EVIDENCE.md
  docs/production/A11Y_PERF_EVIDENCE.md
  docs/production/FINAL_READINESS_REPORT.md
  docs/production/BACKUP_RESTORE_EVIDENCE.md
  docs/production/ROLLBACK_EVIDENCE.md

CURRENT KNOWN RISKS

P0:
- core-cloudflared.service reportedly crash-loops.
- Production traffic currently depends on a manually started
  Cloudflare Tunnel connector.
- Tunnel token is reportedly exposed in process arguments.
- Reboot may interrupt public access.

P1:
- Terraform lock reportedly remains from a previous plan.
- zWorkforce infrastructure must be reconciled with the
  current approved Git branch.
- zMovie binds to 0.0.0.0:8080, currently mitigated by UFW.

P2:
- PostgreSQL integration tests remain skipped.
- Full CI/CD and release provenance are incomplete.
- SBOM and image vulnerability scanning are incomplete.
- Full authenticated browser E2E requires completion.
- Accessibility and load acceptance require updated evidence.

DO NOT treat the reported state as independently verified.
Preserve all valid credentials, deployment settings and active
services unless a verified security defect requires changes.
Do not recreate the License Server (existing source:
services/license-server/).

============================================================
3. GLOBAL SAFETY RULES
============================================================

Never:

- Run git reset --hard against user work.
- Force push or force-merge failing checks.
- Delete production data or Terraform state.
- Force-unlock Terraform (use the supported backend recovery
  process after explicit operator approval).
- Kill the only healthy Cloudflare connector before cutover.
- Print, log or commit real secrets (passwords, tokens, license
  keys, private signing keys, tunnel credentials, full env files).
- Extract credentials from process command lines (/proc, ps output).
- Copy active process environment variables containing secrets.
- Reboot the production server without explicit approval.
- Restart unrelated production services unnecessarily.
- Run destructive database migrations without approval.
- Activate real payment capture without approval.
- Enable live ticket sales without approval.
- Enable public automatic publication without approval.
- Bypass required checks or alter unrelated repositories.

Every production change must include:

1. Current-state inspection.
2. Impact and dependency analysis.
3. Configuration backup.
4. Validation before modification.
5. Controlled application.
6. Post-change health checks.
7. Tested rollback procedure.
8. Timestamped evidence.

Use feature branches and focused PRs for new code.
Record exact commands, timestamps, commit SHAs, tests and actual results.

If a task requires destructive changes, pause that specific
operation for operator approval and continue other safe work.
If a step is blocked, complete every other independent, safe task.

============================================================
PHASE 0 — BASELINE VERIFICATION
============================================================

Inspect the current repositories:

  git status --short
  git branch --show-current
  git rev-parse HEAD
  git fetch origin
  git log -5 --oneline

Check local versus remote state.

Inspect the documentation listed in section 2.

Inspect active services:

  systemctl status
  journalctl
  ss -tlnp
  nginx -t
  cloudflared version
  terraform version
  running database services
  active deployment configuration

Do not expose sensitive arguments or environment values
in logs or reports.

Identify:

- Healthy production services.
- Existing failing services.
- Which process owns each listening port.
- Existing runtime environment files.
- Current rollback capability.
- Git changes requiring preservation.

Classify findings as:

  VERIFIED
  IMPLEMENTED_NOT_VERIFIED
  DEFECTIVE
  BLOCKED

Create:

  docs/production/PRODUCTION_CLOSEOUT.md

Record confirmed status and outstanding gates.
Create a new timestamped evidence directory outside Git.

============================================================
PHASE 1 — P0: CLOUDFLARE TUNNEL RECOVERY (ZERO-DOWNTIME)
============================================================

GOAL

Restore reliable, automatically managed Cloudflare connectivity.
Production traffic must no longer depend on a manually launched
connector containing a tunnel token in command-line arguments.

STEP 1 — READ-ONLY DISCOVERY

Identify:

- The active Cloudflare Tunnel and tunnel identity.
- The healthy connector(s) and active connector count.
- The failing systemd service and why it fails
  (missing EnvironmentFile, missing CLOUDFLARE_TUNNEL_TOKEN,
  incorrect service user, file permissions, invalid command
  syntax, incorrect tunnel credentials, conflicting
  configuration, incorrect tunnel ID, duplicate instances).
- Existing tunnel credentials and credential source.
- Cloudflare service configuration and ingress routes.
- The actual installed cloudflared version and its supported
  secure credential-delivery mechanisms.

Inspect journal errors without displaying credentials.

STEP 2 — SECURE CREDENTIAL DELIVERY

Reuse the existing approved tunnel.
Do not create a replacement tunnel unless necessary.

Choose a supported mechanism such as a restricted tunnel
credential file or systemd credential facility:

- Restrictive file ownership and permissions.
- Dedicated service identity where compatible.
- No literal token in ExecStart.
- No token in environment diagnostics, Git, process command
  arguments, or application logs.

Validate the actual supported cloudflared invocation
before changing the service.
Do not invent unsupported token-file arguments.

Never recover the token by copying it from /proc or ps output.
Never place the token directly in ExecStart arguments.

If no securely stored authorized credential is available,
report the missing secret and request its approved provisioning.

STEP 3 — PREPARE MANAGED REPLACEMENT

Create a sanitized and versioned systemd configuration template.
Store actual credentials outside Git and outside document roots.

Validate:

- Restricted file ownership and permissions.
- Correct tunnel ID and ingress configuration.
- Correct service account and automatic restart behavior.

If the existing tunnel and Cloudflare account support multiple
simultaneous connectors, start the managed connector in parallel.
Keep the working manual connector running.

Verify:

- Managed connector is healthy with correct tunnel identity.
- Correct hostname ingress for all affected production hostnames.
- WordPress route, zMovie root and License API work.
- No unexpected redirect loops or connection failures.

Test:

  https://zmovie.zeaz.dev/
  https://zmovie.zeaz.dev/cinema/
  https://license.zeaz.dev

STEP 4 — CONTROLLED CUTOVER

Keep the current healthy connector running while preparing
and validating the managed replacement.
Start the replacement only after validating its configuration.

Only after the managed connector passes all checks:

- Confirm new connector health, stability and expected tunnel
  connector registration.
- Confirm systemd restart behavior.
- Perform controlled traffic continuity checks.
- Perform a controlled retirement of the manual process.
- If the managed connector fails, retain or restore the
  known-good connector immediately.

Never interrupt the only working connector prematurely.
Do not revoke the old credential before confirming the
replacement is operational.

STEP 5 — TOKEN EXPOSURE RESPONSE

Treat a token exposed through process arguments as potentially
compromised according to the organization's security policy.
Plan safe credential rotation using the approved Cloudflare
management workflow.
Preserve service continuity during rotation.
Validate the new credential and revoke the old credential
only after a successful cutover.

STEP 6 — REBOOT READINESS

Verify (use the actual service name discovered on the host):

  systemctl is-enabled <tunnel-service>
  systemctl is-active <tunnel-service>

Verify restart behavior, dependency ordering, credential access,
network recovery, connector health and log rotation.
Prepare an operator-approved reboot acceptance test.
Do not perform a production reboot without operator approval.
If authorized, execute a controlled reboot drill with
pre-reboot backup, connectivity checks and rollback access.

DELIVERABLES

  Secure systemd unit
  Redacted configuration template
  Deployment runbook
  Rollback runbook
  Service health evidence

ACCEPTANCE GATE

- Managed connector is healthy and starts automatically.
- No tunnel token is present in the managed service's argv.
- Existing production hostnames remain accessible.
- Failed connector and duplicate process issues are resolved.
- Recovery is documented.

============================================================
PHASE 2 — P1: TERRAFORM STATE AND LOCK RECOVERY
============================================================

Inspect:

  <zworkforce-repo>/infrastructure/terraform/cloudflare

Determine:

- Current branch and local modifications.
- Remote differences (origin/main vs working branch).
- Actual Terraform backend.
- Current lock owner and lock timestamp.
- Current Terraform processes and pending infrastructure changes.

Never assume a lock is stale based only on its age.
Never use terraform force-unlock.
Never remove lock files or database lock records manually.
Do not delete state or lock files blindly.
Do not run concurrent Terraform operations against the same state.

If another legitimate Terraform operation holds the lock:

- Do not interrupt it.
- Do not run a competing apply.
- Record the owner and blocked operation.
- Continue other independent phases.

If the previous operation has finished but a lock remains:

- Collect evidence and identify the authorized owner.
- Prepare a documented recovery procedure.
- Obtain explicit approval before unlocking (supported backend
  recovery process only).

After safe lock resolution:

  terraform fmt -check -recursive
  terraform validate
  terraform state list
  terraform plan

Confirm:

  zmovie.zeaz.dev (cloudflare_dns_record.zmovie)
  license.zeaz.dev (license hostname record)
  existing Cloudflare Tunnel
  correct origin routing
  required DNS records
  expected ingress order
  existing unrelated services
  zero unexpected destruction

Avoid duplicate records and unrelated infrastructure changes.
Reconcile the feature branch with zworkforce/main through
a focused PR respecting branch protection.

Do not perform destructive Terraform apply without approval.
Do not apply a plan containing unexpected production changes.
Do not duplicate resources already present in state.

DELIVERABLE

  Terraform state reconciliation report
  Reviewed plan summary
  Infrastructure PR
  Import/recovery evidence if applicable

ACCEPTANCE GATE

- Terraform operations are no longer blocked.
- Code, state and live resources agree.
- Plan has no unexpected changes.
- Required zMovie and License DNS/tunnel resources are versioned.
- GitHub CI passes.

============================================================
PHASE 3 — POSTGRESQL STAGING INTEGRATION
============================================================

The previous test suite reported:

  178 tests passed.
  2 PostgreSQL tests skipped (ZMOVIE_PG_DSN not set).

Investigate the exact skipped tests.

Do not invent or request production PostgreSQL credentials
when an isolated integration environment is sufficient.
Do not migrate production data during this phase.
Do not migrate live ticketing data or enable real ticket
sales without a separately approved migration plan.

FIRST: inspect the real PostgreSQL requirements in:

  services/cinema-api/
  Commerce modules
  Ticketing modules
  Existing migrations
  Existing test fixtures

Verify that the application and migrations genuinely support
PostgreSQL rather than merely containing a portable-looking schema.

CREATE AN ISOLATED TEST DATABASE with:

  separate test database
  separate database user
  isolated credentials (disposable, test-only)
  restricted network binding (loopback only)
  no production data and no production credentials
  reproducible migrations

Prefer Docker Compose or an equivalent isolated setup.
Use synthetic data only.

Configure ZMOVIE_PG_DSN only in the isolated test environment.
Do not commit the real DSN or password.

Execute:

  existing PostgreSQL integration tests
  migrations
  transaction rollback tests
  concurrency tests (actual concurrent DB connections,
    multiple application workers where applicable)
  backup and restore checks

Verify:

- Schema migrations.
- Transaction isolation.
- Concurrent seat holds (a seat cannot be sold twice).
- Unique seat constraints.
- Idempotent confirmation (duplicate requests cannot issue
  duplicate tickets).
- Expired holds cannot generate valid purchases.
- Failed transactions release resources correctly.
- Rollback behavior.
- Database connection failure recovery.
- Backup and isolated restore.
- No impact on the existing MySQL WordPress database.

Inspect the current SQLite-based Cinema API architecture.
If the PostgreSQL implementation is incomplete, implement
the production-compatible adapter and migrations while
preserving existing SQLite test compatibility.
Do not rely on SQLite passing as evidence of PostgreSQL
transactional correctness.

DELIVERABLE

  PostgreSQL integration configuration
  Test fixtures
  Migration evidence
  Concurrency test evidence
  Database backup/restore runbook

Do not switch the production database without a separate
reviewed migration and explicit operator approval.

ACCEPTANCE GATE

- PostgreSQL integration tests pass.
- Existing SQLite tests continue passing.
- Concurrency tests prove no double-selling.
- Migration and rollback evidence is recorded.

============================================================
PHASE 4 — COMPLETE CI AND SECURITY TOOLCHAIN
============================================================

Inspect the existing GitHub Actions workflows and dependency
lock files, cache and CI workflows.
Reuse existing successful workflows.
Do not create duplicate workflows unnecessarily.
Do not modify application requirements merely because a
package download failed.

Complete (union worklist):

1. Python test matrix.
2. Pytest availability.
3. Ruff lint.
4. PHP lint.
5. JavaScript syntax and test coverage.
6. ShellCheck.
7. WordPress integration tests.
8. PostgreSQL integration tests.
9. Docker image build (compose validation).
10. Dependency vulnerability scanning (pip-audit).
11. Container vulnerability scanning.
12. SBOM generation.
13. Secret scanning.
14. Release checksums.
15. Release provenance.
16. Staging deployment validation.
17. Production promotion gate.

Use maintained tools compatible with the existing project.
Use approved package sources and verified package integrity.
Use least-privilege GitHub Actions permissions.
Pin critical third-party Actions appropriately.
Keep deployment secrets in an approved secret-management system.
Do not echo secrets into logs.

If the toolchain cannot be installed because of network
problems, investigate package availability and approved
offline dependency caches.
Create reproducible toolchain installation instructions.
Add the missing CI jobs as independently reviewable changes.

SECURITY GATES

  No committed secrets.
  No unauthorized private keys.
  No unexpected vulnerable production dependencies.
  No critical image vulnerabilities without documented exception.
  SBOM generated for release artifacts.
  Build provenance recorded.
  CI artifacts retained according to project policy.

Do not suppress failing scanners to obtain green checks.
Do not bypass required security checks to produce a green result.
If a vulnerability has no available fix, document: affected
package, installed version, advisory, actual exposure,
mitigation, owner and deadline.

DELIVERABLE

  CI workflow updates
  Security evidence
  SBOM artifacts
  Reproducible toolchain instructions

ACCEPTANCE GATE

- All required CI checks pass.
- Container scans are complete.
- SBOM is generated and retained.
- Release artifacts are reproducible and traceable.
- Production deployment cannot bypass approval.

============================================================
PHASE 5 — FULL AUTHENTICATED END-TO-END ACCEPTANCE
============================================================

Use the existing isolated staging environment.
Do not perform destructive authentication or payment
tests against real production users.
Do not revoke the production license during testing.
Create disposable test identities and synthetic content:

  anonymous viewer
  registered viewer
  creator / licensed creator
  administrator

Every test must clean up its own synthetic data.
Capture redacted screenshots and test logs.
Do not include session cookies or tokens in artifacts.

Execute Playwright tests covering:

WORDPRESS

- Login and logout.
- Film search and genre filtering.
- Vertical feed and video playback.
- Favorites and favorite removal.
- Creator submission and rights acknowledgment.
- Pending moderation and administrator approval.
- Wrong-user access rejection.
- Invalid REST nonce rejection.
- Expired session rejection.
- Unauthorized favorites mutation rejection.
- Creator-only operation rejection.

LICENSE

- Valid creator entitlement.
- Expired license.
- Revoked license.
- Wrong site and wrong product / audience.
- Missing entitlement.
- Invalid signature (forged).

COMMERCE SANDBOX

- Plan selection and sandbox checkout.
- Duplicate webhook and invalid webhook signature.
- Failed payment simulation and refund simulation.
- Subscription cancellation and entitlement revocation.

TICKETING SANDBOX

- Seat selection and seat hold.
- Concurrent booking and hold expiration.
- Duplicate confirmation.
- Sandbox ticket generation, QR validation, check-in.
- Cancellation and refund states.

BROWSER MATRIX

  Desktop Chromium
  Mobile viewport
  Keyboard-only navigation
  Reduced-motion preference

Record screenshots only for successfully executed flows.
Redact all credentials and personal data.

ACCEPTANCE GATE

All critical authenticated and authorization scenarios pass.

============================================================
PHASE 6 — MEDIA PIPELINE AND PERFORMANCE
============================================================

Read the existing docs/production/A11Y_PERF_EVIDENCE.md.
Do not repeat already completed tests without a reason.
Do not reimplement completed work.

Validate:

  Authorized uploads
  File-size restrictions
  MIME validation
  Media probing (FFprobe)
  FFmpeg processing
  Poster and thumbnail generation
  Worker retries and processing failures
  Queue recovery and storage quotas
  Rights enforcement and editorial approval

If real model weights or accelerated hardware are unavailable:

  Complete deterministic non-model tests.
  Preserve existing CPU fallback.
  Mark accelerated real-model evidence BLOCKED.
  Do not invent model-output evidence.

PERFORMANCE

Measure (TTFB, LCP, CLS, INP, REST API latency, license
activation latency, MySQL/PostgreSQL latency, media-processing
throughput, API latency, database transaction latency, booking
concurrency, frontend responsiveness, queue recovery).

Run controlled load tests against staging with reproducible
parameters.
Do not stress-test production without specific approval.

Propose reasonable service-level objectives and ask for
operator approval before treating them as formal SLOs.

============================================================
PHASE 7 — ACCESSIBILITY AND PRIVACY ACCEPTANCE
============================================================

Review existing accessibility evidence before rerunning tools.
Target WCAG 2.2 AA-oriented acceptance.

Run the remaining required checks:

- Automated axe checks.
- Keyboard-only navigation.
- Focus visibility and order.
- Screen-reader review and screen-reader controls.
- Reduced motion.
- Form labels and errors.
- Video captions where required.
- Color contrast.
- Mobile touch targets.
- Responsive layouts.
- Accessible authentication flows.

Test both Thai and English interfaces where supported.
Fix real defects.
Document all remaining exceptions.

For privacy, validate:

- Account data export and deletion.
- Authentication and reauthentication.
- Data ownership checks.
- PII redaction and audit-log minimization.
- Retention and authorized backup handling.

Do not include real customer data in automated fixtures.
Do not claim WCAG 2.2 AA compliance without sufficient
automated and manual audit evidence.

============================================================
PHASE 8 — RELEASE AUTOMATION
============================================================

Create or improve the existing release pipeline:

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

Implement or complete:

  staging deployment
  pinned release artifacts
  predeployment checks
  migration checks
  database backup
  application smoke tests
  rollback on failure
  release manifest
  deployment audit trail

Add a release manifest containing:

  application commit
  WordPress plugin version
  WordPress theme version
  License Server version
  Cinema API version
  migration version
  container image digests
  deployment timestamp
  rollback reference

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

Deploy to staging and validate the entire stack.
Do not deploy arbitrary feature-branch code directly to production.
Do not automatically promote staging to production without
the required approval.
Do not enable unrestricted auto-update of custom
WordPress plugins or themes.
Preserve the existing WordPress and zMovie deployment
architecture unless a change is justified.

============================================================
PHASE 9 — SECURITY AND AVAILABILITY HARDENING
============================================================

FIRST PRIORITY — network binding review:

  Active zMovie listener: 0.0.0.0:8080 (currently mitigated by UFW).

Determine whether binding to all interfaces is actually
necessary. Check systemd configuration, Nginx proxying,
container networking and UFW.

Do NOT restart production merely to change this value.
The existing UFW configuration currently restricts exposure.

Add defense-in-depth when a safe maintenance window is available.
Prefer loopback binding (127.0.0.1:8080) when the application is
accessed only through a local reverse proxy.
Validate Nginx upstream connectivity before changing the binding.
Apply through an approved controlled restart window.
Preserve the existing firewall until the new binding
and routing have been verified.

ALSO AUDIT

- MySQL binding and permissions.
- License administration endpoint access (network edge AND
  application layer).
- WordPress REST authentication.
- PHP-FPM secret delivery.
- File upload security and media URL SSRF protections.
- Sandbox payment secrets, Cinema API admin token, QR signing key.
- Sensitive service logs and runtime file/directory permissions.
- Database credential exposure.
- Backup encryption and access.
- Secret scanning in CI.

Review firewall exposure, reverse-proxy trust boundaries,
Cloudflare Tunnel access, authentication, session handling,
rate limiting, secrets ownership, log retention and
backup permissions.

Run dependency and code security checks.
Fix confirmed High/Critical findings before release.
Do not replace verified runtime secrets without a documented
rotation requirement.

No public endpoint may return secrets or private diagnostics.

============================================================
PHASE 10 — BACKUP, RESTORE AND DISASTER RECOVERY
============================================================

Inspect the existing backup and rollback evidence.
Preserve currently functioning backup jobs.
Do not create duplicate schedules.

Verify:

  WordPress database backup
  zMovie data backup (production AND staging)
  License Server database backup
  Cinema API state backup
  Ticketing and Commerce data stores
  Media assets
  Configuration recovery
  Protected key recovery and signing-key recovery procedures
  Cloudflare configuration

Ensure database and application backups are consistent
at a documented recovery point.
Review retention and off-host backup copies.
Check backup checksums and scheduled alerting.

Store key material through an independently secured backup
mechanism.
Do not place unencrypted private keys in general backup archives.

Execute an isolated restore using synthetic or sanitized data
for every supported durable database.
Do not overwrite production.
Validate restored data and service startup.

Test:

- Database restore.
- WordPress recovery.
- Application code rollback.
- License API recovery.
- Cinema API recovery.
- Lost media-storage availability.
- Failed deployment rollback.

Record measured RPO/RTO evidence (actual measurements).
Do not fabricate recovery metrics.
Set up actionable monitoring and alerting.

Document how to recover after:

  Host reboot
  Cloudflare connector failure
  Database corruption
  Lost application container
  Invalid deployment
  Signing-key compromise
  Expired or unavailable TLS certificate

============================================================
PHASE 11 — FEATURE AND SECURITY CLOSEOUT
============================================================

Use the existing FEATURE_MATRIX as the source of truth.
Update existing documentation instead of creating
duplicate conflicting reports.

For every feature, record:

  implementation path
  dependency
  tests
  integration status
  operational status
  deployment status
  evidence

Inspect and close remaining safe gaps in:

  Studio-to-Cinema integration
  Creator dashboard
  Media processing
  Membership management
  Privacy export/delete
  Cinema administration
  Content moderation
  Search and filtering
  Monitoring and alerting

Avoid rewriting features that already pass their tests.

Continue to keep these explicitly disabled:

  real payment capture
  live ticket sales
  automatic public film publication

These require separate legal, financial, operational and
production authorization.

============================================================
PHASE 12 — GITHUB DELIVERY AND FINAL VERIFICATION
============================================================

Use focused branches and PRs. Adapt branch names to actual
repository conventions. Suggested workstreams:

  fix/cloudflared-managed-service
  fix/terraform-zmovie-reconciliation
  fix/terraform-state-reconciliation
  harden/zmovie-network-boundaries
  test/postgres-cinema-integration
  test/postgres-integration
  ci/release-supply-chain
  ci/release-security-evidence
  test/cinema-authenticated-e2e
  ops/release-automation
  ops/production-recovery-closeout

Use conventional commits. Keep unrelated changes out of each PR.
Run applicable tests and CI before merging.
Respect branch protection. Never bypass required checks.
Do not claim a PR was merged unless GitHub confirms it.
Do not alter unrelated repositories.
Use GPG signing when available.

Do NOT commit:

  .env
  private keys
  tunnel credentials
  passwords
  Terraform state
  database dumps
  production backups
  unredacted diagnostic logs

After changes, perform a full regression assessment:

PUBLIC ROUTES

  https://zmovie.zeaz.dev/
  https://zmovie.zeaz.dev/cinema/
  https://zmovie.zeaz.dev/cinema/wp-json/
  https://license.zeaz.dev

BACKEND

  zMovie readiness
  License API health
  WordPress runtime
  MySQL
  Cinema API
  PostgreSQL staging

INFRASTRUCTURE

  Cloudflare Tunnel
  Nginx
  PHP-FPM
  UFW
  Terraform
  systemd service enablement
  backup cron
  monitoring

SECURITY

  no exposed production credentials
  least-privilege runtime
  no public DB ports
  valid TLS
  signed lease verification
  RBAC
  REST authorization
  private media access
  secure webhook handling

RELEASE

  tests green
  staging green
  image scan green
  SBOM generated
  release manifest created
  rollback validated

Never declare production-ready based on HTTP 200 alone.

============================================================
REQUIRED FINAL REPORT (THAI)
============================================================

Provide a complete Thai report with:

1. Repository states and current commits.
2. Cloudflare Tunnel recovery: previous failure, root cause,
   exact fix, new managed service, verified traffic continuity,
   token rotation status, reboot-readiness evidence.
3. Terraform: backend, lock status, drift results, code changes,
   plan summary, PR and CI evidence.
4. Security: network binding, credentials, service privileges,
   vulnerability findings.
5. Database: PostgreSQL setup, integration tests, migration tests,
   rollback evidence, production migration blockers.
6. CI/CD: test results, container scan, SBOM, release provenance.
7. Functional E2E: WordPress, License, Commerce sandbox,
   Ticketing sandbox.
8. Accessibility and performance results.
9. Backup/restore and rollback results.
10. Outstanding blockers and operator decisions.

For every production gate, use:

  VERIFIED
  IMPLEMENTED_NOT_VERIFIED
  BLOCKED
  NOT_APPLICABLE

Include actual timestamps, test counts, exit codes, sanitized
evidence paths, commit SHAs, PR URLs and CI links.
Never invent evidence.

============================================================
START EXECUTION NOW
============================================================

Execution order:

1. Reconcile the actual environment (baseline verification).
2. Secure and stabilize Cloudflared (zero-downtime recovery).
3. Inspect Terraform lock without force-unlocking.
4. Complete independent PostgreSQL testing.
5. Finish CI and security toolchain.
6. Execute authenticated staging E2E.
7. Complete remaining accessibility and performance tests.
8. Implement release automation.
9. Perform recovery verification.
10. Update the final production evidence.

Begin with Phase 0 baseline verification.
Preserve the existing working connector while preparing
a secure systemd-managed replacement.
Then investigate the Terraform lock without force-unlocking.
Proceed through all remaining safe phases, implement missing
functionality and report actual verification results.
Do not stop after creating documentation.
Stop before unapproved destructive or irreversible operations.
