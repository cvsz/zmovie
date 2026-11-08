# Gap Analysis — zMovie Enterprise Audit

**Baseline SHA:** `67023e1a5a4f69f5154ac19c58b5e390154f3d91`  
**Branch:** `feat/zmovie-enterprise-production-hardening`

## Identified gaps

| # | Gap | Severity | Disposition |
|---|-----|----------|-------------|
| G1 | WordPress feed returned `films` instead of consumed `items` (KeyError) | High (release blocker) | Fixed — `items` + `page`/`per_page`/`total`/`has_more`; `/films` alias; 8 regression tests |
| G2 | Real-model render throughput / media output integrity not evidenced | High (readiness blocker) | Open — requires operator-supplied model/GPU + ffprobe validation |
| G3 | Bilibili public publication not confirmed (`remote_confirmation=true`) | High (readiness blocker) | Open — real publish runbook required |
| G4 | Off-host encrypted backup + restore not validated | Medium | Open — isolated restore test needed |
| G5 | Cloudflare Tunnel token blocked | Medium | Open — admin action required |
| G6 | YouTube publishing deferred | Low (by design) | On roadmap |
| G7 | Live WordPress/PHP runtime not tested in this environment | Medium | Open — run feed contract on staging WordPress |

## Closed by this audit

- G1 (WordPress feed contract).

## Remaining

G2–G7 require operator/external action and are documented in `docs/audit/residual-risks.md`.
