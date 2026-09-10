# zMovie release and synchronization guide

This project uses evidence-backed releases. A reviewed commit, a green local
suite, hosted CI, production-host deployment health, real-model execution and
external publication are separate claims that must not be conflated.

## Prepare the change

Before committing, inspect the complete diff and scope:

```bash
git status --short --branch
git diff --check
git diff --stat
git diff --name-only
```

Do not stage `.env*`, credentials, browser storage, generated caches,
databases, media, private host paths, or unrelated worktree changes.

## Durable-upgrade gate

Before upgrading a native production host, check whether long-running work can
be safely preserved:

```bash
sudo zmovie-ctl upgrade-readiness
sudo zmovie-ctl worker-status
sudo zmovie-ctl worker-jobs
```

An active claimed/running worker lease or an ambiguous external publication
transition blocks an unattended upgrade. Queued work is durable in SQLite and
may remain queued across a normal upgrade. Do not kill a renderer or re-create
a publication package merely to make an upgrade proceed.

## Sign commits

When repository policy requires signed commits, use the configured project
identity and verify the resulting signature. Do not rewrite historic commits
merely to alter their signature.

## Verify before push

Run the repository-defined checks, including:

```bash
python3 -m compileall -q zmovie.py app.py main.py zmovie_platform tests
python3 -m unittest discover -s tests -v
python3 scripts/verify_docs.py
make help >/dev/null
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

Use the isolated declared dependency environment when the system interpreter
does not provide project requirements. Do not weaken Ruff, dependency audit,
ShellCheck, frontend syntax, test, documentation or container-build gates to
obtain a green result.

## Synchronize remote state

Fetch before comparing refs:

```bash
git fetch origin
git rev-parse HEAD origin/main
git log --oneline origin/main..HEAD
git log --oneline HEAD..origin/main
```

If `origin/main` moved, reconcile the branch with review. Never force-push to
bypass remote history or required checks. Use a topic branch and pull request
when direct main updates are protected.

## Hosted CI gate

A PR is mergeable only after GitHub Actions is successful for the exact final
PR head. After merge, retrieve the resulting `main` SHA and verify the push
workflow for that exact SHA. Record the SHA, workflow run number/URL and each
important job conclusion. A successful older commit does not satisfy this gate.

## Native deployment acceptance

After repository and exact-SHA CI are green, update the target checkout and run
the upgrade only when `upgrade-readiness` is safe:

```bash
git fetch origin
git switch main
git pull --ff-only
git rev-parse HEAD
sudo bash ./install.sh upgrade

systemctl is-enabled zmovie
systemctl is-active zmovie
systemctl is-enabled zmovie-worker
systemctl is-active zmovie-worker
systemctl is-enabled zmovie-backup.timer
systemctl is-active zmovie-backup.timer
systemctl is-enabled zmovie-watchdog.timer
systemctl is-active zmovie-watchdog.timer

sudo zmovie-ctl status
sudo zmovie-ctl health
sudo zmovie-ctl doctor
sudo zmovie-ctl worker-status
sudo zmovie-ctl watchdog-status
sudo zmovie-ctl backup-status
```

The native installer provisions a distinct hardened worker and does not weaken
the web service's device isolation. A production-host deployment is not runtime
verified until these commands succeed on that host.

## Renderer and reboot acceptance

Use [Vulkan renderer](VULKAN_RENDERER.md) to test `/dev/dri`, render/video
groups, `vulkaninfo` and `sd-cli --list-devices` in the worker-user context.
Then perform a controlled worker restart against a safe test job and verify that
queue state persists, stale work reconciles and no duplicate execution occurs.
A full server reboot is a separate stronger gate and must not be performed while
an external publication transition is ambiguous.

## Real-model evidence

Do not auto-download large model weights as part of release. If compatible
operator-supplied video weights exist, configure the maintained renderer, run a
small explicit smoke, validate the resulting real video with FFprobe and record
its SHA256 plus runtime evidence. If weights are absent, record real-model
evidence as pending rather than manufacturing success. See [Runtime evidence](RUNTIME_EVIDENCE.md).

## External publication gate

Implementation/release authorization is not Bilibili publication authorization.
A specific prepared package must still pass exact-package human approval and
the existing explicit `CONFIRM-PUBLISH` boundary. `submitted`, `published` and
`remotely confirmed` remain separate states. External completion requires a
genuine public Bilibili video URL bound with `remote_confirmation=true`.

## Rollback

Prefer a new corrective commit or a reviewed revert. Preserve the failed
artifact, logs and exact SHA for diagnosis. Restore persistent data only from a
known verified backup after stopping the affected services and validating the
target state. Never discard durable queue or publication evidence just to force
a rollback through.
