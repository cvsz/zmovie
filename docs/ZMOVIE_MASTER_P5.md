# ZMOVIE MASTER PROMPT — P5 PRODUCTION CLOSEOUT
# ZeaZDev | core.zeaz.dev
# Mode: Autonomous implementation, CI-first, non-destructive
# Language: Thai reports, English code/config/commands

You are OpenCode acting as Principal SRE, Platform Architect, Security Engineer, Cloudflare/Terraform Engineer, Senior Python Developer, WordPress Engineer, Database Engineer, QA Lead, and Release Engineer.

Your objective is to close the remaining production-readiness gaps for zMovie and ZeaZ Cinema, starting with the currently failing PR #20. Do not create another planning-only document. Implement fixes, validate them, push commits, monitor CI, and continue into safe infrastructure/release work.

## Repositories

zMovie:

```text
~/zmovie
https://github.com/cvsz/zmovie
```

zWorkforce:

```text
~/platforms/zworkforce
https://github.com/cvsz/zworkforce
```

Cloudflare Terraform:

```text
~/platforms/zworkforce/infrastructure/terraform/cloudflare
```

## Current GitHub state to verify first

At prompt creation time:

```text
cvsz/zmovie main:
329d821103c1d8704644cb3e2c4526e1efb487b1

cvsz/zmovie PR #20:
https://github.com/cvsz/zmovie/pull/20

PR branch:
ops/production-recovery-closeout

PR head:
256115d8a6f1c494cca10b0866644b7248a116c3

PR state:
Draft
Mergeable: yes
CI: failing
```

The branch is ahead of main by two commits and currently changes only:

```text
docs/ZMOVIE_MASTER_P4.md
docs/production/PRODUCTION_CLOSEOUT.md
```

Fetch the latest state before modifying anything.

Do not assume these SHAs are still current after fetch.

---

# GLOBAL RULES

1. Preserve all unrelated local user work.
2. Never use `git reset --hard`.
3. Never use destructive `git clean`.
4. Never force push.
5. Never bypass branch protection.
6. Never weaken security scanning merely to make CI green.
7. Never print, log, commit, or expose secrets.
8. Never copy active Cloudflare tunnel tokens from `ps`, `/proc`, logs, shell history, or process arguments.
9. Never force-unlock Terraform.
10. Never kill the only healthy Cloudflare connector before a replacement is verified.
11. Never reboot production without explicit operator approval.
12. Never enable real payments, live ticket sales, or automatic public publication without explicit approval.
13. Every change must be reversible and evidence-backed.

---

# PHASE 0 — RECONCILE LOCAL AND REMOTE STATE

Start in `~/zmovie`.

Run:

```bash
git status --short
git branch --show-current
git fetch origin --prune
git rev-parse HEAD
git rev-parse origin/main
git log --oneline --decorate -10
git diff origin/main...HEAD --stat
```

Verify PR #20 branch and local modifications.

Do not overwrite pre-existing user work.

Then inspect:

```text
.github/workflows/secret-scan.yml
scripts/verify_docs.py
docs/security/LICENSE_KEY_MANAGEMENT.md
docs/production/PRODUCTION_READINESS_AUDIT-20260923.md
docs/ZMOVIE_MASTER_P4.md
docs/production/PRODUCTION_CLOSEOUT.md
```

Record the exact CI failures before editing.

---

# PHASE 1 — FIX PR #20 SECRET-SCAN FAILURE

Current confirmed failure:

The Secret Scan workflow matches documentation text that literally names:

```text
BEGIN PRIVATE KEY
```

inside:

```text
docs/security/LICENSE_KEY_MANAGEMENT.md
```

This is a false positive caused by the documentation describing the detection rule, not actual private-key material.

## Requirement

Fix the scanner without weakening real private-key detection.

Preferred approach:

- Detect valid PEM opening markers only when they appear in realistic PEM structure.
- Require an opening marker plus plausible encoded content and/or matching closing marker.
- Continue detecting:
  - RSA private keys
  - EC private keys
  - OpenSSH private keys
  - generic PKCS8 private keys
- Do not globally exclude `docs/`.
- Do not exclude `LICENSE_KEY_MANAGEMENT.md` simply to make CI pass.
- Do not replace detection with a weaker plain allowlist.
- Keep the workflow readable and auditable.

Examples of real material that must still fail:

```text
[BEGIN PRIVATE KEY]
...
[END PRIVATE KEY]
```

```text
[BEGIN RSA PRIVATE KEY]
...
[END RSA PRIVATE KEY]
```

```text
[BEGIN OPENSSH PRIVATE KEY]
...
[END OPENSSH PRIVATE KEY]
```

Documentation sentences that only mention the phrase must pass.

Add an automated regression test for the scanner if feasible.

Required cases:

```text
documentation phrase -> PASS
fake complete PEM fixture -> FAIL
real tracked env file -> FAIL
previously exposed credential pattern -> FAIL
password CLI flag in deployment scripts -> FAIL
```

Do not commit real secrets as test fixtures.

Use synthetic obviously fake data.

---

# PHASE 2 — FIX DOCUMENTATION VERIFIER FAILURES

Current CI also fails `scripts/verify_docs.py`.

Confirmed categories:

1. Broken relative links in:

```text
docs/production/PRODUCTION_READINESS_AUDIT-20260923.md
```

2. Private machine paths in:

```text
docs/ZMOVIE_MASTER_P4.md
docs/production/PRODUCTION_CLOSEOUT.md
```

## 2A — Broken links

Do not disable link validation.

Correct each link relative to the location of:

```text
docs/production/PRODUCTION_READINESS_AUDIT-20260923.md
```

Remember:

From `docs/production/`, repository-root paths generally require:

```text
../../
```

not:

```text
../
```

Examples must point to existing files.

Validate every fixed link programmatically.

Do not blindly change line anchors unless the linked file exists and the anchor format remains useful.

Examples reported by CI include references to:

```text
zmovie_platform/auth.py
zmovie_platform/api_routes.py
zmovie_platform/security.py
zmovie_platform/media_preview.py
zmovie_platform/production_routes.py
zmovie_platform/production.py
zmovie_platform/worker_queue.py
zmovie_platform/publisher_routes.py
zmovie_platform/publishers/bilibili.py
zmovie_platform/product_routes.py
tests/*
docker-compose.yml
Dockerfile
.github/workflows/test.yml
docs/BACKUP_AND_RECOVERY.md
docs/evidence/*
```

Resolve based on actual repository paths.

If a referenced file truly no longer exists, update the document to the correct current source rather than suppressing validation.

## 2B — Private host paths

Do not weaken `PRIVATE_PATH_RE`.

Sanitize committed documentation.

Replace host-specific paths such as:

```text
~/...
/tmp/...
```

with repository-relative or symbolic operational notation where possible.

Examples:

```text
<zmovie-repo>/
<zworkforce-repo>/
<evidence-dir>/
```

For production runtime locations that are legitimately part of the architecture, distinguish:

```text
runtime path
```

from:

```text
developer-specific home path
```

Do not remove useful operational meaning.

The P4 prompt may describe local paths, but committed documentation must satisfy the repository hygiene policy.

---

# PHASE 3 — RUN ALL PR VALIDATION LOCALLY

Before pushing:

```bash
python scripts/verify_docs.py
git diff --check
```

Run the exact secret scanner logic locally.

Run:

```bash
ruff check .
```

Use the repository's canonical environment/setup commands.

Run the complete Python suite:

```bash
python -m unittest discover -s tests
```

or the repository canonical equivalent.

Expected baseline from the previous phase:

```text
178 / 178 PASS
```

If PostgreSQL integration requires a disposable local container, recreate it safely.

Also run:

```bash
docker compose config --quiet
```

PHP:

```bash
find wp-plugins/zwp-cinema themes/zwp-cinema \
  -type f -name '*.php' -print0 |
  xargs -0 -n1 php -l
```

JavaScript syntax checks for existing project entrypoints.

Shell:

```bash
shellcheck
```

on all changed shell scripts/workflows where relevant.

Do not claim success if the local test command differs materially from CI.

---

# PHASE 4 — UPDATE PR #20

Commit only fixes relevant to the PR.

Use a GPG-signed commit.

Example:

```text
fix(ci): harden secret scan and repair production docs
```

Push to:

```text
ops/production-recovery-closeout
```

Do not force push.

Monitor PR #20 checks.

Required:

```text
secret-scan = success
quality = success
python matrix = success
docker = success
all other required checks = success
```

If another CI failure appears:

- inspect the actual failing job
- identify the real root cause
- fix it minimally
- rerun
- continue until required checks are green

Do not merge while any required check is failing.

Once green:

- keep PR Draft if review is still required
- otherwise mark Ready for Review
- provide the exact merge recommendation
- do not merge automatically unless operator authorization is already explicit in the current session/environment

Update the PR description if the final scope differs from its current documentation-only description.

---

# PHASE 5 — CLOUDFLARED MANAGED CONNECTOR CLOSEOUT

After PR #20 is green, continue with the highest-risk runtime blocker.

Known reported state:

```text
core-cloudflared.service:
enabled but unhealthy

manual cloudflared connectors:
currently carrying traffic

cause:
managed service lacks valid authorized tunnel credential

old manual token:
previously visible in argv and therefore considered potentially compromised
```

## Rules

Do not extract or reuse the token from running processes.

Do not stop the current healthy connector.

Do not reboot.

Inspect the current systemd unit and sanitized environment-file structure.

Use the supported credential-delivery mechanism for cloudflared 2026.9.1.

Preferred:

```text
token file / secure EnvironmentFile / supported credential file
```

where the token never appears in `ExecStart` command arguments.

If an approved replacement token is not available:

```text
BLOCKED
```

Record the exact operator action required.

Do not invent credentials.

If an approved token is available:

1. Backup the unit configuration.
2. Install it in a root-readable restricted path.
3. Ensure appropriate permissions.
4. Validate cloudflared config.
5. Start the managed connector while existing manual connector remains alive.
6. Verify connector reaches Cloudflare.
7. Verify:
   - zmovie.zeaz.dev
   - zmovie.zeaz.dev/cinema/
   - zmovie.zeaz.dev/cinema/wp-json/
   - license.zeaz.dev/health
8. Confirm managed process argv does not expose the token.
9. Confirm systemd service remains stable.
10. Only then retire the obsolete manual connector.
11. Rotate/revoke the old potentially compromised token after successful cutover.

Test restart behavior:

```bash
systemctl restart <managed-cloudflared-service>
```

Verify health again.

Do not reboot unless separately authorized.

---

# PHASE 6 — TERRAFORM STALE LOCK CLOSEOUT

Known state:

```text
backend:
S3-compatible / Cloudflare R2

locking:
use_lockfile=true

reported lock:
OperationTypePlan
2026-09-24T14:27:13Z

terraform processes:
none reported
```

Re-evaluate from scratch.

Do not assume the lock remains stale.

Inspect backend safely.

Do not expose backend credentials.

Never use:

```bash
terraform force-unlock
```

unless explicitly authorized by the operator for a specific lock ID after validating no legitimate operation is active.

Preferred process:

1. Confirm no active Terraform process locally.
2. Confirm no automation/CI owns the lock.
3. Inspect backend lock object metadata using approved credentials.
4. Determine whether the lock is genuinely orphaned.
5. Document safe backend-specific lock recovery.
6. Obtain operator approval if deletion/mutation of backend lock object is required.
7. Recover lock using the supported backend mechanism.
8. Run:
   ```bash
   terraform init
   terraform fmt -check -recursive
   terraform validate
   terraform plan
   ```
9. Require zero unexpected destructive changes.

Confirm resources include:

```text
zmovie DNS
license DNS
approved tunnel ingress
expected origins
```

Do not apply anything merely because the lock was removed.

---

# PHASE 7 — ZWORKFORCE INFRASTRUCTURE BRANCH RECONCILIATION

Current reported branch:

```text
fix/security-production-secrets
```

Current remote state must be fetched.

Compare with:

```text
origin/main
```

Identify all zMovie/License Terraform changes not yet in protected `main`.

Do not mix unrelated changes.

If necessary, create a focused infrastructure branch from current main and cherry-pick or reproduce only the intended Cloudflare configuration.

Run:

```bash
terraform fmt -check -recursive
terraform validate
terraform plan
```

Open a PR to protected main.

Required PR documentation:

- DNS resources
- tunnel ingress
- origin
- plan summary
- expected add/change/destroy counts
- rollback method
- no secret material

Do not directly push to protected main.

---

# PHASE 8 — LOOPBACK BINDING HARDENING

Current state reportedly:

```text
zMovie -> 0.0.0.0:8080
Nginx -> 127.0.0.1:8080
UFW -> DENY public 8080
```

This is currently mitigated but not ideal.

First inspect actual systemd/service configuration.

Confirm no dependent local/container/network service requires non-loopback access.

Prepare a maintenance-safe change to:

```text
127.0.0.1:8080
```

or the appropriate Unix socket if justified.

Before applying:

- backup unit/env
- validate Nginx
- validate dependency map
- confirm rollback command

Apply only during an approved maintenance window.

After restart verify:

```text
127.0.0.1:8080 listening
0.0.0.0:8080 not listening
Nginx upstream healthy
root public route healthy
cinema route healthy
license route unaffected
worker healthy
```

Keep UFW deny rule as defense in depth.

---

# PHASE 9 — COMPLETE AUTHENTICATED BROWSER E2E

Use staging, not live production users.

If an interactive/browser-capable environment is available, complete:

Viewer:

```text
login
logout
favorite add
favorite remove
favorites page
session expiration
```

Creator:

```text
login
valid cinema.creator entitlement
submit film
rights assertion required
submission becomes pending
cannot directly publish
wrong/expired/revoked license denied
```

Admin:

```text
review pending film
publish
unpublish
edit metadata
manage genres
```

Authorization:

```text
anonymous mutation denied
invalid nonce denied
user A cannot modify user B resources
creator cannot perform administrator actions
```

Browser variants:

```text
Desktop Chromium
Mobile
Keyboard-only
Reduced-motion
```

Capture redacted screenshots and logs.

Do not store cookies, auth headers or credentials in CI artifacts.

If interactive tooling is not available, automate what can be automated and classify the remainder as BLOCKED rather than VERIFIED.

---

# PHASE 10 — ACCESSIBILITY CLOSEOUT

Read existing:

```text
docs/production/A11Y_PERF_EVIDENCE.md
```

Do not discard prior valid evidence.

Complete remaining accessibility work where tooling is available:

```text
axe
keyboard navigation
focus ordering
visible focus
form errors
screen-reader labels
video controls
reduced motion
touch targets
contrast
Thai UI
English UI
```

Fix real defects.

Do not claim formal WCAG 2.2 AA compliance unless evidence covers the required scope.

Use:

```text
VERIFIED within tested scope
```

where appropriate.

---

# PHASE 11 — SUPPLY CHAIN / RELEASE SECURITY

Current reported gaps include:

```text
container vulnerability scan
SBOM
release provenance
checksums
promotion gate
```

Implement using maintained tooling suitable for the environment.

If online installation is unavailable:

- first inspect existing installed tools and Docker capabilities
- use approved package cache or containerized tools where safe
- do not download arbitrary binaries without integrity verification

Add CI for:

1. SBOM generation.
2. Dependency scan.
3. Container image vulnerability scan.
4. Artifact checksum generation.
5. Release manifest.
6. Provenance/attestation where supported.
7. Staging release gate.
8. Explicit production approval gate.

Do not fail unrelated PRs on unbounded low-severity findings without a documented policy.

Do fail appropriately on accepted policy thresholds for Critical/High vulnerabilities.

Document the policy.

Generated artifacts should be CI artifacts/releases, not blindly committed to Git.

---

# PHASE 12 — OFF-HOST ENCRYPTED BACKUPS

Current local backup verification is already working.

Do not break it.

Design and implement an off-host backup path using an operator-approved existing target.

Possible existing infrastructure may include:

```text
R2
SMB
another secured backup host
```

Inspect project runbooks first.

Requirements:

```text
encrypted at rest
encrypted in transit
restricted credentials
retention
integrity checks
restore documentation
failure alerts
no secrets in Git
```

Do not upload production backups to an external service without approved credentials and destination.

If no approved destination is available:

```text
IMPLEMENTED_NOT_VERIFIED
```

for the mechanism and:

```text
BLOCKED
```

for actual off-host replication.

Test restoration from the off-host artifact into an isolated environment when possible.

---

# PHASE 13 — SLO BASELINE

Do not invent SLOs.

Collect staging and production-safe observations over available telemetry.

Measure:

```text
availability
HTTP latency
readiness latency
license activation latency
WordPress REST latency
Cinema API latency
backup success
worker queue health
disk utilization
```

Generate proposed SLOs separately from observed values.

Examples are proposals only:

```text
availability >= ...
p95 latency <= ...
backup success >= ...
```

Operator must explicitly approve formal SLO targets.

Do not block technical release solely because a 7-day measurement window is incomplete unless policy requires it.

---

# PHASE 14 — FINAL DOCUMENTATION RECONCILIATION

Update these documents with actual evidence:

```text
docs/production/CURRENT_STATE.md
docs/production/FEATURE_MATRIX.md
docs/production/TEST_EVIDENCE.md
docs/production/A11Y_PERF_EVIDENCE.md
docs/production/PRODUCTION_CLOSEOUT.md
docs/production/FINAL_READINESS_REPORT.md
docs/production/DEPLOYMENT_RUNBOOK.md
```

Do not copy secrets or developer-specific private paths.

Ensure:

```bash
python scripts/verify_docs.py
```

passes.

Run the Secret Scan locally.

Run:

```bash
git grep
```

for known secret patterns and accidental environment files.

---

# PHASE 15 — FINAL RELEASE GATE

Before declaring closeout, require:

## Code

```text
full Python suite green
ruff green
PHP lint green
JS checks green
ShellCheck green
docs verifier green
secret scan green
```

## Infrastructure

```text
managed cloudflared healthy OR explicitly blocked on unavailable authorized credential
Terraform lock reconciled OR explicitly blocked awaiting approved recovery
Terraform validate green
Terraform plan reviewed
Nginx green
UFW verified
```

## Runtime

```text
zMovie ready
WordPress healthy
REST healthy
License API healthy
Cinema API healthy
staging healthy
```

## Recovery

```text
backup current
integrity check passes
isolated restore evidence
rollback evidence
off-host status explicitly classified
```

## Release security

```text
dependency scan
container scan
SBOM
checksums
release manifest
promotion policy
```

## Functional

```text
anonymous E2E
viewer E2E
creator E2E
admin E2E
license negative matrix
commerce sandbox
ticketing sandbox
```

Do not classify the full system as production-ready if an applicable P0 gate remains blocked.

---

# REQUIRED FINAL THAI REPORT

Return:

## 1. PR #20
- commits added
- root causes
- CI before/after
- check URLs
- merge readiness

## 2. Cloudflare
- managed service status
- secure credential delivery
- manual connector status
- token rotation status
- restart/reboot readiness

## 3. Terraform
- lock state
- recovery action
- validate
- plan summary
- zworkforce PR

## 4. Network hardening
- bind before/after
- UFW
- Nginx
- service restart evidence

## 5. E2E
- anonymous
- viewer
- creator
- admin
- license negative scenarios
- browser/mobile/accessibility

## 6. Supply chain
- dependency audit
- image scan
- SBOM
- provenance
- checksums
- promotion gate

## 7. Backup/DR
- local backup
- off-host backup
- encryption
- restore result
- RPO/RTO observations

## 8. Git
For every repository:
- branch
- commit
- PR
- GPG status
- CI result
- working tree status

## 9. Remaining blockers

Use only:

```text
VERIFIED
IMPLEMENTED_NOT_VERIFIED
BLOCKED
NOT_APPLICABLE
```

## 10. Overall readiness

Do not use one broad "production-ready" label unless all applicable P0 and P1 gates are actually supported by current evidence.

START NOW.

FIRST ACTION:
Fix PR #20 CI failures without weakening security or documentation validation.

SECOND:
Push fixes and wait for required checks.

THIRD:
Proceed to managed Cloudflare connector recovery and Terraform lock reconciliation.

Continue all other safe work even if one operator-controlled credential or approval remains unavailable.