# Worker Queue Review — zMovie Enterprise Audit

**Baseline SHA:** `67023e1a5a4f69f5154ac19c58b5e390154f3d91`  
**Branch:** `feat/zmovie-enterprise-production-hardening`

## Implementation summary

The durable queue lives in SQLite (`worker_jobs`) and is implemented in `zmovie_platform/worker_queue.py` with the worker loop in `zmovie_platform/worker.py`.

## Verified behaviors

| Behavior | Status | Notes |
|----------|--------|-------|
| Enqueue | Pass | Atomic insert, sanitized payload (rejects secret-like fields), idempotent job id |
| Claim | Pass | `BEGIN IMMEDIATE` transaction + conditional `UPDATE ... WHERE status IN ('queued','retry_wait')`; rowcount checked to prevent double-claim |
| Heartbeat | Pass | Renews `heartbeat_at` and `lease_expires_at`; returns boolean success |
| Mark running | Pass | Transition guarded by `worker_id` and `status='claimed'` |
| Complete | Pass | Sets `completed`, writes `result_json`, clears lease |
| Fail / retry | Pass | `attempts` incremented; `retry_wait` if under `max_attempts`, else `failed`; `next_attempt_at` bounded by `retry_delay_seconds` |
| Stale lease recovery | Pass | `recover_stale(apply=True)` at worker startup; expires `claimed`/`running` jobs; bilibili → `recovery_required`, others → `retry_wait` or `failed` |
| Pause / resume | Pass | `runtime_state.worker_paused` gate in `serve()` |
| Queue status | Pass | `queue_status()` returns paused + per-status counts |
| Payload sanitization | Pass | Sensitive keys rejected (`password`, `secret`, `token`, `cookie`, `authorization`, `browser_state`, `storage_state`) |

## Delivery semantics

**At-least-once with idempotent completion.** A job is claimed under a lease; if the worker crashes before completing, the lease expires and `recover_stale` returns it to `retry_wait`/`failed` for re-processing. Side-effect handlers (render, publish) must be idempotent keyed by `idempotency_key`/`job_id` to avoid duplicate side effects on redelivery. This is documented in the code; consumers must enforce idempotency at the handler layer.

## Tests

`tests/test_worker_queue.py` — 13 test cases covering enqueue/get/list roundtrip, claim and heartbeat, mark_running/complete, fail (retry and exhausted), `recover_stale` (bilibili → recovery_required, render → retry_wait), pause/resume, `queue_status` shape, and `sanitize_payload` rejection of secret fields and unsupported types. All pass.

## Residual notes

- Duplicate enqueue of the same logical work is not deduplicated at the queue layer; callers must supply an idempotency key and handlers must be idempotent.
- Database interruption mid-job is handled per-transaction; the caller is responsible for reconciling in-flight external state (render/publish) after restart.
