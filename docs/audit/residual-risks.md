# Residual Risks — zMovie Enterprise Audit

**Baseline SHA:** `67023e1a5a4f69f5154ac19c58b5e390154f3d91`  
**Branch:** `feat/zmovie-enterprise-production-hardening`

The following risks remain after this audit. None are Critical or High security findings from this review, but each must be accepted or mitigated by the operator before production promotion.

## R1 — Real-model video render not evidenced

**Risk:** Accelerated video throughput and render determinism depend on operator-supplied model weights, ComfyUI/SDCPP renderer, and GPU. Not verified in this audit.  
**Mitigation:** Operator must run a real render and validate output with ffprobe (resolution, aspect ratio, frame rate, codec, A/V sync, subtitle sync) before declaring the media pipeline production-ready.  
**Owner:** Media pipeline engineer / operator.

## R2 — Bilibili public publication not confirmed

**Risk:** Bilibili submission flow is implemented (prepare → approve → preflight → publish → confirm), but real publication requires a confirmed public URL and `remote_confirmation=true`. Not confirmed.  
**Mitigation:** Complete the real publish runbook and record durable publication evidence. Auto-publish remains `false` by default.  
**Owner:** Publishing engineer / operator.

## R3 — Cloudflare Tunnel token blocked

**Risk:** Public ingress via Cloudflare Tunnel is blocked pending administrator token.  
**Mitigation:** Obtain the tunnel token from the admin and configure; do not expose internal worker APIs publicly.  
**Owner:** Operator / SRE.

## R4 — Off-host backup and restore not validated

**Risk:** Daily SQLite backups are configured (14+ retention), but off-host encrypted backup destination and restore validation against production-like data were not tested.  
**Mitigation:** Perform isolated restore tests (never against production data) and document RPO/RTO.  
**Owner:** SRE / DBA.

## R5 — YouTube publishing deferred

**Risk:** YouTube publishing is intentionally deferred until Bilibili completion evidence exists.  
**Mitigation:** Track on `docs/YOUTUBE_ROADMAP.md`; do not enable until Bilibili gate passes.  
**Owner:** Product / publishing engineer.

## R6 — Local `.env` contains generated credentials

**Risk:** The working tree contains an untracked, gitignored `.env` with generated admin credentials and secret key. It must never be committed.  
**Mitigation:** `.env` is in `.gitignore` and not tracked; secret scan confirms no tracked secrets. Rotate generated credentials before first production use.  
**Owner:** Operator.

## R7 — Empty WordPress feed handled; runtime WordPress not tested here

**Risk:** Feed contract fixed and unit-tested, but no live WordPress/PHP runtime was available in this environment to execute the plugin end-to-end.  
**Mitigation:** Run the feed contract against a real WordPress staging instance (populated, empty, invalid pagination, both aliases) before WordPress release.  
**Owner:** Integration engineer / QA.
