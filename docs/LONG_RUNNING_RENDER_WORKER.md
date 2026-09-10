# Long-running render worker

zMovie separates web/API lifetime from long-running production execution. The web service validates a production request, creates the production run, persists a durable `worker_jobs` record in SQLite, and returns. `zmovie-worker.service` claims the job and executes the production stages.

## Durable states

Worker jobs use `queued`, `claimed`, `running`, `retry_wait`, `completed`, `failed`, `cancelled`, and `recovery_required`. Claims are serialized with a SQLite `BEGIN IMMEDIATE` transaction. A claimed/running job has a worker identity, heartbeat and lease expiry. The worker renews the lease while it owns the job.

On startup the worker reconciles stale leases. Local render work may move to `retry_wait` while retry budget remains. Work that may have crossed an external publishing boundary must not be blindly retried; ambiguous external work is moved to `recovery_required`.

## ComfyUI recovery

For ComfyUI, zMovie checkpoints the remote `prompt_id` and `client_id` into the render-job metadata immediately after `/prompt` succeeds. A recovered render reuses that checkpoint and queries `/history/{prompt_id}` instead of submitting a second prompt. This sharply reduces duplicate remote inference after worker/service restarts.

## Production flow

`POST /api/v2/projects/{project_id}/production/run` now enqueues durable work. The worker executes the existing strict production flow: render, production-media validation, assembly, Bilibili package preparation, export, then stops at the approval gate. It never approves or publishes Bilibili automatically.

## Operations

```bash
sudo zmovie-ctl worker-status
sudo zmovie-ctl worker-jobs
sudo zmovie-ctl worker-job WRK_ID
sudo zmovie-ctl worker-recover --dry-run
sudo zmovie-ctl worker-recover --apply
sudo zmovie-ctl worker-pause
sudo zmovie-ctl worker-resume
sudo zmovie-ctl worker-restart
sudo zmovie-ctl worker-logs 200
```

A software test proving the queue state machine is not the same as reboot evidence. Production restart/reboot acceptance must be performed on the actual server and recorded separately.
