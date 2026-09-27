
# ZMOVIE P6 — CI RECOVERY AND MANAGED INFRASTRUCTURE

Act as the principal release engineer and SRE.
Implement and verify the following work in order.

1. FIX ZMOVIE PR #20 CI

   Current head: 0c6755c
   PR: https://github.com/cvsz/zmovie/pull/20

   Python CI:
   - Install ffmpeg and ffprobe in the Python CI jobs.
   - Verify both binaries before running tests.
   - Run the complete test matrix on Python 3.11–3.14.
   - Preserve the existing media integration tests.

   Supply-chain CI:
   - Investigate the Trivy v0.65.0 installation failure.
   - Verify binary download, integrity and runner compatibility.
   - Fix the installation mechanism without bypassing scanning.
   - Retain the HIGH/CRITICAL vulnerability policy.
   - Verify that an actual image scan completes.
   - Retain the already working SBOM and release manifest jobs.

   Recheck all workflows on the exact final commit.

2. UPDATE PR #20

   The current PR description incorrectly describes a
   documentation-only change.

   Update it to reflect the actual implementation,
   security improvements, tests and remaining blockers.

   Keep Draft until all required checks pass.
   Do not merge automatically.

3. RECONCILE ZWORKFORCE

   Fetch the latest protected main branch.

   Compare it with fix/security-production-secrets.
   Preserve the existing Terraform and security changes.
   Avoid duplicating already merged changes.

   Prepare a focused PR for remaining Cloudflare
   configuration, with validation evidence.

4. RECOVER MANAGED CLOUDFLARED

   Preserve the existing healthy manual connectors.

   Use only securely provisioned authorized credentials.
   Never extract tokens from existing processes.

   Validate the managed service and public traffic
   before retiring manual connectors.

   Rotate the previously exposed token after an
   approved and verified cutover.

5. TERRAFORM AND PRODUCTION SAFETY

   Investigate the existing backend lock.
   Do not force-unlock or remove it without approval.

   Keep production reboots, destructive Terraform
   operations and live database migrations blocked
   until separately authorized.

6. FINAL EVIDENCE

   Report:
   - Exact GitHub commit and PR status.
   - Every CI job and its verified conclusion.
   - Actual image vulnerability findings.
   - Cloudflared managed-service health.
   - Terraform drift and lock state.
   - Remaining production blockers.

   Do not declare production-ready while the managed
   tunnel recovery gate remains unresolved.
