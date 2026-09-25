# Supply Chain Policy — zMovie release artifacts

Canonical policy for container scanning, SBOM, checksums and promotion.
Applies to `.github/workflows/supply-chain.yml`.

## 1. Vulnerability thresholds

| Severity | Fix available | Policy |
|---|---|---|
| Critical | yes | **Blocking.** Release stops. |
| High | yes | **Blocking.** Release stops. |
| Critical | no | Reported as a tracked exception; requires owner + deadline. |
| High | no | Reported as a tracked exception; requires owner + deadline. |
| Medium | any | Reported only. Never blocks an unrelated pull request. |
| Low | any | Reported only. |

Rationale: blocking on unbounded Medium/Low noise trains operators to bypass
the gate, which is worse than reporting. Blocking on fixable Critical/High is
the standard, actionable bar.

## 2. Exception record

An unfixable Critical/High finding is accepted only with a written record
containing: affected package, installed version, advisory identifier,
actual exposure in this deployment, mitigation, owner and review deadline.
No exception may be granted by disabling the scan job.

## 3. Required artifacts

Every release produces, as CI artifacts (never committed to Git):

- `zmovie-sbom.cdx.json` — CycloneDX SBOM of the production image
- `sbom.sha256` — SHA-256 of the SBOM
- `release-manifest.json` — commit, component versions, migrations, image
  digest, checksums, rollback references and blocked-feature gates
- `trivy-all.json` — full advisory report including Medium/Low

Retention: 90 days.

## 4. Action pinning

Third-party actions in the supply-chain workflow are pinned to commit SHAs
that were resolved and verified against the upstream repositories at the time
of authoring. Floating tags are not acceptable here. When bumping an action,
resolve the tag to a commit and verify the commit exists before committing.

## 5. Gates

```text
sbom + manifest  ─┐
image scan       ─┼─> staging gate ─> production promotion (manual, protected env)
staging compose  ─┘
```

`production-promotion` runs only on `workflow_dispatch` with an explicit
opt-in, and it targets the protected `production` environment. It performs
no automated production change; it prints the reviewed commit and the
operator-run upgrade command. Promotion therefore cannot be bypassed by a
green build alone.

## 6. Explicitly blocked regardless of scan results

These require separate legal, financial, operational and production
authorization and are never enabled by a supply-chain change:

- real payment capture
- live ticket sales
- automatic public film publication

## 7. Local reproduction

```bash
docker build -t zmovie:supply-chain .
.venv/bin/python scripts/release-manifest.py --image zmovie:supply-chain
# optional, if trivy is available:
trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 zmovie:supply-chain
```
