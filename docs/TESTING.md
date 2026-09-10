# zMovie testing and verification

Tests prove the scope they exercise. This page distinguishes deterministic
repository checks from hosted CI, production-host runtime, real-model, reboot,
and external publication evidence.

## Isolated setup

Use a clean virtual environment for the declared dependency set:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip wheel
./.venv/bin/python -m pip install -r requirements.txt
```

If repository bytecode caches are not writable, use
`PYTHONDONTWRITEBYTECODE=1` or an isolated `PYTHONPYCACHEPREFIX` outside the
checkout. Do not add the environment, generated cache, database, media, or
browser state to Git.

## Local checks

The main Makefile/repository checks are:

```bash
python3 -m compileall -q zmovie.py app.py main.py zmovie_platform tests
python3 -m unittest discover -s tests -v
python3 scripts/verify_docs.py
make help >/dev/null
make lint
make audit
node --check static/app.js
node --check static/studio-preview.js
node --check static/hyperframes-studio.js
node --check static/durable-worker.js
node --check static/product.js
bash -n install.sh scripts/install-resilient-runtime.sh scripts/zmovie-ctl.sh
shellcheck --severity=warning install.sh install-docker.sh scripts/*.sh
docker compose config --quiet
docker build -t zmovie:test .
git diff --check
```

Use the repository-defined CI workflow as the final authority for hosted checks.
Do not remove or weaken a gate merely to make it green.

## Durable queue and recovery coverage

The worker tests exercise durable queue creation, serialized atomic claiming,
double-claim prevention, running-state transition, heartbeat lease renewal,
completion, bounded retry/exhaustion, stale lease recovery, pause/resume and
credential-like payload rejection. The external-transition test verifies that
a stale Bilibili-type job becomes `recovery_required` rather than a normal
retry.

ComfyUI tests include the recovery invariant: when a render job already carries
a remote `prompt_id`, provider execution reconciles `/history/{prompt_id}` and
does not call `/prompt` again. This is deterministic software evidence; a real
remote renderer restart still requires production-host acceptance testing.

Backup tests verify creation through SQLite's online backup API and the
validated backup inventory. Watchdog tests verify that missing renderer/model
readiness is not treated as a service-restart reason and that repair selection
is constrained to unhealthy service boundaries.

## CI gates

The GitHub workflow keeps a Python 3.11–3.14 matrix, documentation validation,
application compilation, durable-runtime CLI smoke checks, product/Studio
frontend JavaScript syntax, installer/operations shell syntax, project tests,
prompt and publisher smoke checks, ComfyUI workflow validation, project-reset
safety, Docker Compose validation, production image build, focused Ruff,
pip-audit, and ShellCheck.

A PR is merge-ready only when the exact current PR head has a completed
successful workflow. After merge, the exact new `main` SHA must pass the push
workflow before it is described as CI verified.

## Production-host acceptance

After CI, the native deployment must independently prove service/timer/runtime
state:

```bash
systemctl is-active zmovie
systemctl is-active zmovie-worker
systemctl is-active zmovie-watchdog.timer
systemctl is-active zmovie-backup.timer
sudo zmovie-ctl health
sudo zmovie-ctl worker-status
sudo zmovie-ctl watchdog-status
sudo zmovie-ctl backup-status
sudo zmovie-ctl renderer-doctor
sudo zmovie-ctl vulkan-status
sudo zmovie-ctl sdcpp-status
```

A controlled worker restart with a safe queued/running test job should prove
that SQLite queue state persists, the worker returns, stale work is reconciled
and no duplicate job executes. A production-host reboot test is a stronger,
separate acceptance step and must not be run during an ambiguous external
publication transition.

## Real-model evidence

Model presence/configuration is not real-model verification. A real video-capable
model must produce an actual file that passes FFprobe with a video stream,
positive duration, positive width/height and non-zero size. Record output
SHA256 and the factual runtime evidence. A black FFmpeg clip, image renamed to
video, metadata JSON, mock result or model-free ComfyUI smoke output does not
satisfy this gate.

## Publication evidence

Bilibili states remain distinct: prepared, approved, submitted, published and
remotely confirmed. Generic implementation authorization does not satisfy the
exact-package approval or explicit `CONFIRM-PUBLISH` gate. External completion
requires a genuine public video URL and `remote_confirmation=true`.

## Reporting results

Record the exact repository SHA, command, interpreter/environment, test count,
skipped tests, warnings and exit code. For hosted CI also record workflow run
number/URL and job conclusions. For production runtime record service/timer,
queue, device/backend and evidence-artifact facts. If a dependency, model,
credential, terminal, hardware device or external confirmation is unavailable,
report the affected gate as pending rather than passing.
