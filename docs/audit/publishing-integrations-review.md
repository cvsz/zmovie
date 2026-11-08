# Publishing Integrations Review — zMovie Enterprise Audit

**Baseline SHA:** `67023e1a5a4f69f5154ac19c58b5e390154f3d91`  
**Branch:** `feat/zmovie-enterprise-production-hardening`

## Summary

Publishing integrations are implemented with explicit human approval gates and fail-closed semantics. No real external publication was confirmed in this audit (requires provider credentials and live platform access, which must not be fabricated).

## Bilibili

| Item | Status |
|------|--------|
| Authentication / browser session state | Implemented; session state treated as credential, never stored in queue payloads; Google password/2FA not accepted |
| Upload workflow | Prepare → approve → preflight → publish → confirm (hardened package flow) |
| Metadata / category / cover | Supported in publish package |
| Publish state tracking | `pub_*` jobs with audit trail; `submitted` is not treated as proof of public |
| Rate limits / retry | Timeout-configurable; failure handling with retry candidates |
| Real publication | Not confirmed — requires `remote_confirmation=true` + confirmed public URL |
| Auto-publish | `ZMOVIE_BILIBILI_AUTO_PUBLISH=false` (default) |
| Runbook | `docs/BILIBILI_REAL_PUBLISH_RUNBOOK.md` |

## YouTube

- Intentionally deferred until Bilibili completion evidence exists (`docs/YOUTUBE_ROADMAP.md`).
- OAuth client id/secret documented as confidential in `.env.example`; not committed.
- Default visibility `PRIVATE`.

## WordPress (ZeaZ Cinema)

- Feed contract fixed: `items` + `page`/`per_page`/`total`/`has_more`, `/feed` and `/films` aliases, deterministic error schema.
- Favorites and creator submission require login + WP REST nonce; license-gated.
- Real WordPress runtime not tested in this environment (no PHP/WordPress instance available).

## General provider rules applied

- Timeouts bounded; retry with bounded backoff where applicable.
- Secrets scoped and redacted from logs.
- No real publishing claimed without verified provider evidence.
- Platform terms and provider restrictions not bypassed.

## Residual risk

Real Bilibili/YouTube publication status must be confirmed against live provider endpoints before those integrations are declared production-ready.
