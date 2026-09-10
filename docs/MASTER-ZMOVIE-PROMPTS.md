# zMovie LONGEST-TASK MASTER EXECUTION PROMPT
# Repository: https://github.com/cvsz/zmovie
# Mode: longest-task / autonomous engineering / evidence-first
# Goal: continue until every safely executable task is complete

You are the principal production/platform engineer responsible for taking
cvsz/zmovie from its CURRENT main branch to a resilient, unattended,
long-running production video server.

DO NOT work from an old remembered SHA.

Repository:
  https://github.com/cvsz/zmovie

Production server:
  hostname: dbc
  OS: Ubuntu 26.04
  LAN interface: ens33
  LAN address: 192.168.3.132/24

Public application:
  https://zmovie.zeaz.dev

CURRENT KNOWN REMOTE BASELINE AT PROMPT CREATION
================================================

Current main was last observed as:

  eac9275badaaeb2de9d6ded39337ace9c76f64c8

Commit:

  feat: add reusable product video studio frontend (#10)

Known latest CI:

  workflow: test
  run: #401
  conclusion: success

However:

DO NOT assume this SHA is still current when execution begins.

Your first operation MUST be to retrieve origin/main again.

Current main includes newer functionality that MUST NOT be regressed:

  /studio
      main production Studio

  /product
      reusable Product Video Studio

  make/product.mk
      reusable product-plan/product-video automation

  Hyperframes creative templates

  one-click Content + Storyboard generation

  production render / assemble / Bilibili prepare / export

  stable-diffusion.cpp CPU/Vulkan provider

  ComfyUI provider

  hardened Bilibili prepare -> approve -> preflight ->
  submit -> remote-confirmation state machine

Preserve all of those capabilities.


==================================================
OPERATING MODE: LONGEST TASK
==================================================

This is intentionally a long-running engineering task.

Do NOT:

- stop after inspecting the repo;
- stop after writing a plan;
- stop after creating one file;
- stop after making one commit;
- stop because a later phase depends on runtime verification;
- repeatedly ask the operator questions when a safe default can be derived;
- mark a task complete merely because code exists.

Continue through every independent phase that can safely be completed.

When one item is blocked by external/manual state:

1. record the precise blocker;
2. preserve its evidence;
3. continue all unrelated tasks;
4. return to the blocked task when possible.

Use iterative checkpoints internally:

  inspect
  design
  implement
  test
  review
  fix
  retest
  document
  commit
  synchronize
  hosted CI
  runtime verification
  external verification

Always prefer completing the implementation over describing how somebody
else could complete it.


==================================================
0. FRESH-PULL / DIVERGENCE GUARD
==================================================

Before editing anything:

  git status --short
  git branch --show-current
  git remote -v
  git fetch origin
  git rev-parse HEAD
  git rev-parse origin/main
  git log --oneline --decorate -15 origin/main

If the local repository is clean and on main:

  git pull --ff-only

If local unrelated changes exist:

DO NOT destroy them.

Record them and use a safe branch/worktree strategy.

Never:

  git reset --hard
  git clean -fd
  force push

unless the operator explicitly authorized destructive cleanup.

Record:

  BASE_SHA=<fresh origin/main SHA>

All implementation decisions must be based on BASE_SHA, not on the SHA
written in this prompt.


==================================================
1. FULL CURRENT-REPO RECONNAISSANCE
==================================================

Inspect the CURRENT implementations before changing architecture.

At minimum inspect:

  install.sh
  Makefile
  make/product.mk

  main.py
  app.py

  static/studio.html
  static/product.html
  static/app.js
  static/studio-preview.js
  product frontend JavaScript/CSS

  zmovie_platform/jobs.py
  zmovie_platform/pipeline.py
  zmovie_platform/production.py
  zmovie_platform/production_routes.py
  zmovie_platform/repository.py
  zmovie_platform/storage.py
  zmovie_platform/migrations.py
  zmovie_platform/health.py
  zmovie_platform/providers.py
  zmovie_platform/sdcpp_provider.py
  zmovie_platform/control_cli.py

  scripts/zmovie-ctl.sh
  scripts/install-sdcpp.sh
  scripts/configure-sdcpp.sh
  scripts/install-comfyui.sh

  all Bilibili publisher modules
  all Bilibili safety/preflight/confirmation scripts

  tests/
  docs/
  .github/workflows/

Search specifically for any implementation already added since this prompt:

  worker_jobs
  worker
  queue
  lease
  heartbeat
  watchdog
  backup.timer
  recovery
  resume
  retry_wait
  Vulkan
  /dev/dri
  runtime evidence
  product studio

Do not duplicate a newer implementation.

Extend/refactor current code instead.


==================================================
2. REMAINING PRODUCTION MISSION
==================================================

Resolve ALL of these areas:

  dbc Vulkan via Studio/worker          incomplete until runtime proven
  Durable render worker                required
  Render recovery after reboot         required
  24/7 watchdog                        required
  Automatic verified backup timer      required
  Real model runtime evidence          required when weights available
  Real Bilibili publication            external completion gate

Additionally preserve and integrate the newer:

  Product Video Studio /product
  reusable Product Video generator
  Hyperframes
  storyboard/content generator
  main Studio one-click production


==================================================
3. TARGET RUNTIME ARCHITECTURE
==================================================

Current long AI execution must NOT depend on the uvicorn process lifetime.

Target:

                         ┌───────────────────────┐
                         │      Internet         │
                         └──────────┬────────────┘
                                    │
                           Cloudflare Tunnel
                                    │
                                    ▼
                         zmovie.zeaz.dev
                                    │
                                    ▼
                ┌────────────────────────────────┐
                │        zmovie.service          │
                │ Web/API/Studio/Product Studio  │
                │ hardened, no GPU privilege     │
                └───────────────┬────────────────┘
                                │
                         durable SQLite queue
                                │
                                ▼
                ┌────────────────────────────────┐
                │     zmovie-worker.service      │
                │                                │
                │ claim                          │
                │ heartbeat                      │
                │ retry                          │
                │ recover                        │
                │ sd-cli                         │
                │ ComfyUI                        │
                │ media validation               │
                └───────────┬────────────────────┘
                            │
                ┌───────────┴───────────────┐
                │                           │
          stable-diffusion.cpp           ComfyUI
          CPU / Vulkan                   local/remote
                │
                ▼
          real generated video
                │
                ▼
             FFprobe QC
                │
                ▼
             Assembly
                │
                ▼
        Bilibili package/export
                │
                ▼
          HUMAN APPROVAL GATE


==================================================
4. WEB SERVICE MUST REMAIN HARDENED
==================================================

Do NOT fix Vulkan by broadly weakening the web service.

Keep:

  zmovie.service

isolated from direct GPU/device requirements.

Where practical retain:

  NoNewPrivileges=true
  PrivateDevices=true
  ProtectSystem=strict
  ProtectHome=true
  ProtectKernelTunables=true
  ProtectKernelModules=true
  ProtectKernelLogs=true
  ProtectControlGroups=true
  RestrictSUIDSGID=true
  LockPersonality=true
  RestrictRealtime=true
  empty CapabilityBoundingSet

The API/Studio should enqueue production work.

It should not own a multi-hour sd-cli child process.


==================================================
5. IMPLEMENT zmovie-worker.service
==================================================

Build a dedicated production worker:

  python -m zmovie_platform.worker

Required behavior:

- service user: zmovie
- Restart=always
- graceful SIGTERM
- persistent queue
- worker identity
- atomic claim
- heartbeat
- lease timeout
- bounded retry
- crash recovery
- structured logs
- no secret logging

GPU/Vulkan access belongs here.

Configure render/video supplementary groups only when available.

Example concept:

  SupplementaryGroups=render video

but installer must correctly handle systems where either group does not exist.

Expose only required device resources.

Target:

  /dev/dri/renderD*

Do not give the worker unnecessary root privileges.


==================================================
6. DURABLE SQLITE JOB QUEUE
==================================================

Replace long production execution launched through process-local
ThreadPoolExecutor with a durable SQLite-backed queue.

ThreadPoolExecutor may remain for genuinely short in-process tasks, but a
multi-minute/hour renderer must never rely on uvicorn lifetime.

Create migrations/schema for durable execution.

Suggested table:

  worker_jobs

Fields should cover at least:

  id
  job_type
  project_id
  production_run_id
  provider
  payload_json

  status
  priority

  attempts
  max_attempts

  worker_id

  claimed_at
  heartbeat_at
  lease_expires_at

  started_at
  next_attempt_at

  completed_at
  failed_at

  result_json

  error_code
  error_message

  created_at
  updated_at

States:

  queued
  claimed
  running
  retry_wait
  completed
  failed
  cancelled
  recovery_required

Implement atomic claiming using SQLite transactions.

Multiple workers must not successfully claim the same job.

Enable/configure SQLite WAL where compatible with existing persistence
architecture.

Never persist credentials/tokens/browser state in job payload_json.


==================================================
7. PRODUCTION RUN DURABILITY
==================================================

One-click Studio production currently logically performs:

  render
  validate
  assemble
  prepare
  export

Change orchestration so durable jobs drive that flow.

Desired:

  POST production/run
        │
        ├── validate request/QC/provider
        │
        ├── create production run
        │
        ├── enqueue durable job
        │
        └── return quickly
                    │
                    ▼
             zmovie-worker
                    │
                    ├── render
                    ├── validate
                    ├── assemble
                    ├── prepare
                    └── export
                    │
                    ▼
              approval_required

Do NOT auto-approve Bilibili.

Do NOT auto-publish Bilibili.


==================================================
8. PRODUCT VIDEO STUDIO INTEGRATION
==================================================

CURRENT main contains:

  /product
  reusable Product Video Studio
  make/product.mk

Do not implement worker infrastructure only for /studio while leaving
/product on a fragile execution path.

Review product workflow architecture.

Where product generation eventually triggers real production:

use the SAME durable production queue.

Architecture:

  Product input
      ↓
  product assessment
      ↓
  content strategy
      ↓
  storyboard/prompts
      ↓
  project
      ↓
  durable production queue
      ↓
  worker
      ↓
  real video
      ↓
  QC/export/publishing package

Do not duplicate renderer stacks.

Studio and Product Studio must share:

  providers
  queue
  worker
  media validator
  assembly
  publication safety
  runtime readiness


==================================================
9. VULKAN SUPPORT ON dbc
==================================================

Production host:

  dbc
  ens33 = 192.168.3.132/24

Do not use:

  cali*
  vxlan.calico
  10.1.x.x

for application addressing.

Implement worker diagnostics for:

  /dev/dri
  render node existence
  render/video groups
  service-user permissions
  vulkaninfo
  sd-cli --list-devices

Commands:

  sudo zmovie-ctl renderer-doctor
  sudo zmovie-ctl vulkan-status
  sudo zmovie-ctl sdcpp-status

The web service should not need /dev/dri access.

The worker should.

For production models use:

  /var/lib/zmovie/models

not:

  /var/lib/zmovie/models/...

because hardened systemd services may use ProtectHome=true.


==================================================
10. stable-diffusion.cpp
==================================================

Preserve current CPU/Vulkan integration.

Do not require NVIDIA/CUDA as a definition of production.

Support:

  auto
  Vulkan
  CPU fallback

Readiness must separate:

  cli_available
  model_configured
  model_files_valid
  video_mode_enabled
  backend
  device_available
  accelerated
  production_ready
  throughput_evidenced

CPU:

  potentially very slow

but:

  CPU != mock
  CPU != invalid

A CPU backend is production-valid only when a REAL configured model generates
a REAL validated video.

Do not use FFmpeg placeholders as AI evidence.


==================================================
11. CRASH / REBOOT RECOVERY
==================================================

Implement leases + heartbeats.

On worker startup inspect stale:

  claimed
  running

jobs.

Provider-aware recovery is mandatory.

LOCAL SD-CLI:

If the renderer process disappeared because the host/service stopped:

  interrupted
  -> retry if safe and within retry budget

COMFYUI:

Persist remote:

  prompt_id

If a worker dies after submitting to ComfyUI:

DO NOT send another prompt first.

Query:

  /history/{prompt_id}

and reconcile the existing execution.

EXTERNAL PUBLISHING:

If Bilibili may have crossed the external submission boundary:

NEVER blindly retry.

Use:

  external_state_unknown
  recovery_required

Require reconciliation.


==================================================
12. WORKER CONTROL COMMANDS
==================================================

Expand:

  sudo zmovie-ctl

with:

  worker-status
  worker-jobs
  worker-job <id>
  worker-recover --dry-run
  worker-recover --apply
  worker-pause
  worker-resume
  worker-restart
  worker-logs

Interactive control panel should expose them too.

Mutation/recovery commands should be fail-safe.


==================================================
13. WATCHDOG
==================================================

Implement:

  zmovie-watchdog.service
  zmovie-watchdog.timer

Check:

  API liveness
  SQLite access
  filesystem writability
  disk free space
  zmovie.service
  zmovie-worker.service
  worker heartbeat if active jobs exist

Optional renderer readiness should be informational unless a render is
actually required.

Important distinction:

  SERVICE HEALTH
  !=
  RENDERER PRODUCTION READINESS

No model configured must NOT trigger restart storms.

Provide:

  zmovie-ctl watchdog-status
  zmovie-ctl watchdog-run

Restart only demonstrably unhealthy components.

Use rate limiting/backoff.


==================================================
14. AUTOMATIC DATABASE BACKUP
==================================================

Implement:

  zmovie-backup.service
  zmovie-backup.timer

Use existing SQLite online backup mechanism.

Required validation:

  PRAGMA quick_check
  PRAGMA foreign_key_check

Atomic write.

Never replace a known-good backup with a failed backup.

Recommended timer:

  daily ~03:15
  Persistent=true
  RandomizedDelaySec=300

Add configurable retention.

Safe default:

  keep at least 14 recent daily backups

Never delete the newest verified backup.

Commands:

  zmovie-ctl backup
  zmovie-ctl backups
  zmovie-ctl backup-status

Make:

  make backup
  make backups
  make backup-status


==================================================
15. UPGRADE DRAIN / RECOVERY
==================================================

Current install/upgrade may restart the service.

That becomes dangerous after long-running rendering exists.

Implement:

  zmovie-ctl upgrade-readiness

Before upgrade detect:

  active worker job
  active local renderer
  ComfyUI remote in-flight execution
  Bilibili ambiguous external transition

Safe policy:

- do not lose work;
- drain if feasible;
- otherwise checkpoint/recover;
- refuse unsafe upgrade when external state cannot be safely reconciled.

Installer upgrades must preserve:

  database
  media
  exports
  publication packages
  models
  Bilibili browser state
  worker queue state
  evidence records

No package regeneration merely because an application upgrade happens.


==================================================
16. REAL MODEL EVIDENCE
==================================================

Do not auto-download huge model weights.

Add:

  zmovie-ctl sdcpp-evidence

Modes:

  inspection only

and explicit:

  --run-smoke

Inspection reports:

  repository SHA
  hostname
  kernel/OS
  sd-cli
  backend
  detected devices
  Vulkan availability
  model configuration
  model readability as zmovie worker
  ffmpeg
  ffprobe
  destination writability

Real smoke must use a real video-capable configured model.

Use intentionally small parameters where supported:

  low resolution
  short duration
  low frame count
  deterministic seed

Result must pass FFprobe:

  real video stream
  duration > 0
  width > 0
  height > 0
  file size > 0

Record:

  SHA256

Write evidence to:

  /var/lib/zmovie/evidence/

Example:

  20260911T...-sdcpp-runtime.json

Evidence must contain facts, not claims.

If model files are absent:

  ENGINE IMPLEMENTED
  MODEL RUNTIME EVIDENCE PENDING

Do not manufacture success.


==================================================
17. PRODUCTION MEDIA GATE
==================================================

Do not weaken existing validation just to make production pass.

A valid production video must have:

  managed path
  actual file
  supported video extension
  successful ffprobe
  video stream
  valid duration
  valid dimensions
  non-empty file

Reject:

  PNG pretending to be video
  metadata JSON
  placeholder output
  mock output
  failed probe
  zero duration

Add codec/FPS/frame facts when available.


==================================================
18. BILIBILI
==================================================

Preserve exact existing safety semantics.

State distinctions:

  prepared != approved
  approved != submitted
  submitted != published
  published != remotely confirmed

Implementation authorization is NOT publication authorization.

Do not auto-submit because this master task was approved.

An exact Bilibili package must be explicitly approved.

External submission requires the repository's existing confirmation gate,
for example:

  CONFIRM-PUBLISH

Before external submission validate:

  exact video
  exact cover
  hashes
  package/manifest
  approval timestamp
  current job state
  authenticated Bilibili-only session
  preflight

After external submit:

If only submission is proven:

  status=submitted
  remote_confirmation=false

STOP external retry.

Reconcile Creator Center first.

Completion requires:

  status=published
  published_url=<REAL BILIBILI PUBLIC VIDEO URL>
  metadata.remote_confirmation=true

Never invent the URL.


==================================================
19. STUDIO UX
==================================================

Update /studio to show durable execution:

  Queued
  Claimed
  Rendering
  Validating
  Assembling
  Preparing Bilibili
  Exporting
  Approval required
  Retry wait
  Recovery required
  Failed
  Completed

Show:

  run id
  worker job id
  provider
  attempt
  stage
  last heartbeat
  safe error reason

Do not expose:

  local filesystem paths
  environment
  secrets
  browser state


==================================================
20. PRODUCT STUDIO UX
==================================================

Preserve and harden current /product.

It must continue supporting reusable product input/planning.

Where useful add production handoff:

  Product Plan
      ↓
  Generate storyboard/project
      ↓
  Open in Production Studio

and optionally:

  Queue production

but only through the same production safety gates.

Do not create an independent unsafe render implementation.


==================================================
21. MAKEFILE
==================================================

Preserve existing Makefile and:

  include make/product.mk

Do not regress current product targets.

Add targets:

  make worker-status
  make worker-jobs
  make worker-recover

  make watchdog-status
  make watchdog-run

  make backups
  make backup-status

  make vulkan-status
  make renderer-doctor

  make sdcpp-evidence

  make upgrade-readiness

Existing expected targets must continue working:

  make full-stack
  make upgrade
  make doctor

  make sdcpp-install
  make sdcpp-config
  make sdcpp-status

  make content
  make hyperframes

  make readiness PROJECT_ID=...
  make production PROJECT_ID=... PROVIDER=...

  product targets from make/product.mk

  make bili-session
  make bili-status
  make bili-approve
  make bili-publish


==================================================
22. INSTALL.SH
==================================================

One native production installation should install:

  zmovie.service
  zmovie-worker.service

  zmovie-watchdog.service
  zmovie-watchdog.timer

  zmovie-backup.service
  zmovie-backup.timer

  /usr/local/bin/zmovie-ctl

Create:

  /var/lib/zmovie/models
  /var/lib/zmovie/evidence

with safe ownership/modes.

Installer must be:

  idempotent
  upgrade-safe
  backup-first
  secret-preserving

Verify services after install.

Do not treat missing model weights as failed web-service installation.


==================================================
23. TEST REQUIREMENTS
==================================================

Add deep tests.

DURABLE QUEUE:

  enqueue
  atomic claim
  double-claim prevention
  heartbeat
  lease expiration
  complete
  fail
  retry
  retry exhaustion
  cancelled
  stale recovery

WORKER:

  executes job
  graceful termination
  recovery
  restart simulation
  provider failure
  corrupted payload handling

COMFYUI:

  existing prompt ID reconciliation
  no duplicate remote submission

VULKAN:

  /dev/dri absent
  inaccessible
  CPU only
  Vulkan detected
  service-user permission

BACKUP:

  valid backup
  corruption rejection
  retention
  newest verified backup preserved

WATCHDOG:

  healthy services
  API dead
  worker dead
  stale active-job heartbeat
  no-model condition does not restart healthy service

PRODUCT STUDIO:

  route still works
  planning API still works
  product target tests remain green
  durable production handoff does not bypass safety

BILIBILI:

  exact approval required
  submitted prevents duplicate submit
  ambiguous state prevents retry
  remote_confirmation requires genuine expected public URL

SECURITY:

  public API path redaction
  no tokens in queue
  no browser state in queue/logs
  no arbitrary managed-path escape


==================================================
24. FULL QUALITY GATE
==================================================

Run all repository-defined checks.

At minimum:

  python3 -m compileall ...
  python3 -m unittest discover -s tests -v

  Ruff
  pip-audit
  ShellCheck

  node --check for all current frontend JS including:
    Studio
    Product Studio
    Hyperframes modules

  documentation verifier

  git diff --check

  docker compose config

  production container build

Validate all systemd units.

Preserve Python CI matrix:

  3.11
  3.12
  3.13
  3.14

Do not remove quality gates to obtain green CI.


==================================================
25. DOCUMENTATION
==================================================

Update current documentation to match ACTUAL architecture.

At minimum:

  README.md
  docs/STATUS.md
  docs/ARCHITECTURE.md
  docs/OPERATIONS.md
  docs/CONFIGURATION.md
  docs/TROUBLESHOOTING.md
  docs/TESTING.md
  docs/RELEASE.md

Add:

  docs/LONG_RUNNING_RENDER_WORKER.md
  docs/VULKAN_RENDERER.md
  docs/BACKUP_AND_RECOVERY.md
  docs/RUNTIME_EVIDENCE.md

README must include:

  stable-diffusion.cpp
  Product Video Studio
  worker
  persistent queue
  recovery
  timers

Do not claim runtime evidence solely because tests pass.


==================================================
26. COMMIT STRATEGY FOR A LONG TASK
==================================================

Prefer small reviewable commits by phase.

Suggested boundaries:

  feat: add durable worker queue

  feat: add long-running render worker

  feat: add worker lease recovery

  ops: add worker Vulkan device access

  ops: add watchdog and backup timers

  feat: add runtime renderer evidence

  feat: expose durable production status in studios

  test: cover long-running production recovery

  docs: document resilient production runtime

Each commit must leave the tree in a coherent state when feasible.

Before each commit:

  git diff --check
  focused tests

Before final push:

  complete test suite


==================================================
27. REMOTE SYNCHRONIZATION
==================================================

Before push:

  git fetch origin

Compare current work against fresh origin/main.

If origin/main moved:

DO NOT force push.

Safely rebase/merge after reviewing changes.

Rerun affected tests.

If repository policy favors PR:

  create/update topic branch
  open PR
  wait for checks
  fix failures
  merge only after green

If authorized direct main is valid:

use a safe non-force push.

After push retrieve exact remote SHA.


==================================================
28. HOSTED CI
==================================================

Do not report CI complete until GitHub Actions is green for the EXACT final
remote SHA.

If CI fails:

inspect the failed job/log;
fix root cause;
push;
repeat.

Do not simply rerun nondeterministic failures indefinitely.

Final CI evidence must include:

  final SHA
  workflow run number
  run URL
  all important job conclusions


==================================================
29. DEPLOY TO dbc
==================================================

When repository + CI are green and terminal access exists:

  cd ~/zmovie

  git fetch origin
  git switch main
  git pull --ff-only

Verify:

  git rev-parse HEAD

Then:

  sudo bash ./install.sh upgrade

Verify:

  systemctl is-enabled zmovie
  systemctl is-active zmovie

  systemctl is-enabled zmovie-worker
  systemctl is-active zmovie-worker

  systemctl is-enabled zmovie-backup.timer
  systemctl is-active zmovie-backup.timer

  systemctl is-enabled zmovie-watchdog.timer
  systemctl is-active zmovie-watchdog.timer

Run:

  sudo zmovie-ctl status
  sudo zmovie-ctl health
  sudo zmovie-ctl doctor
  sudo zmovie-ctl worker-status
  sudo zmovie-ctl watchdog-status
  sudo zmovie-ctl backup-status


==================================================
30. dbc VULKAN ACCEPTANCE
==================================================

Verify:

  ip -4 addr show ens33

Expected:

  192.168.3.132/24

Then:

  ls -la /dev/dri
  getent group render
  getent group video
  id zmovie

Run in the SAME security context as the worker where possible:

  sudo -u zmovie vulkaninfo --summary
  sudo -u zmovie sd-cli --list-devices

Then:

  sudo zmovie-ctl renderer-doctor
  sudo zmovie-ctl vulkan-status
  sudo zmovie-ctl sdcpp-status

Do not mark Vulkan verified before dbc proves it.


==================================================
31. REBOOT ACCEPTANCE
==================================================

A durable worker feature is not complete until restart behavior is tested.

Create a safe controlled test job.

Observe state.

Then test controlled worker restart.

Verify recovery.

Where authorized, test a server reboot with a safe test workload.

Expected:

  database state persists
  queue persists
  worker returns
  stale job is reconciled
  no duplicate job executes
  final state is deterministic

Do not conduct destructive reboot testing during an unknown Bilibili
submission transition.


==================================================
32. REAL MODEL ACCEPTANCE
==================================================

Check:

  /var/lib/zmovie/models

If no compatible model exists:

report:

  REAL MODEL EVIDENCE = PENDING
  REASON = no operator-supplied model bundle

Continue all other work.

If compatible weights exist:

validate licensing/config/readability;
configure sdcpp;
run explicit real evidence smoke.

Then verify output with ffprobe.

Record evidence + SHA256.

A black FFmpeg test video is NEVER acceptable as real model evidence.


==================================================
33. BILIBILI FINAL GATE
==================================================

After the application side is complete:

inspect existing publish jobs.

Do not regenerate an already approved package unless required.

Do not reuse an approval for changed media.

Run:

  session validation
  status
  exact-package preflight

External publication is allowed only under explicit exact-package publish
confirmation.

If submitted:

do not resubmit.

If Creator Center produces a real public URL:

bind it through hardened confirmation.

Only then:

  status=published
  published_url=<real URL>
  metadata.remote_confirmation=true

Until then:

  EXTERNAL PUBLICATION = PENDING


==================================================
34. FINAL COMPLETION MATRIX
==================================================

Final response must provide:

ITEM                               CODE   CI   dbc RUNTIME   EXTERNAL
Durable SQLite worker queue        ...
zmovie-worker.service              ...
Vulkan worker isolation            ...
Render restart recovery            ...
ComfyUI remote reconciliation      ...
24/7 watchdog                      ...
Automatic backup timer             ...
Backup integrity/retention         ...
Studio durable queue UI            ...
Product Studio integration         ...
stable-diffusion.cpp integration   ...
Real model execution evidence      ...
Bilibili safety flow               ...
Real Bilibili publication          ...

Also report:

  original BASE_SHA
  final SHA
  commit list
  files changed
  test commands
  test totals
  CI run
  systemd service status
  timer status
  queue status
  worker status
  Vulkan status
  selected backend
  model evidence path
  generated media SHA256
  Bilibili job state
  genuine public URL if any


==================================================
35. STRICT EVIDENCE DEFINITIONS
==================================================

IMPLEMENTED
  code exists

LOCAL VERIFIED
  local test/check passed

CI VERIFIED
  hosted CI passed exact SHA

RUNTIME VERIFIED
  actual dbc command/output proves it

REAL MODEL VERIFIED
  real model produced real video and FFprobe passed

SUBMITTED
  external platform accepted a submission request

PUBLISHED
  publication state exists

REMOTELY CONFIRMED
  genuine public URL was validated and recorded

Never combine these states.


==================================================
36. STOP CONDITIONS
==================================================

Do not voluntarily stop while there are independent executable tasks left.

A valid final stop occurs only when:

A. all repository/code/test/docs/CI work is complete;

AND

B. every available runtime check has been executed;

AND

C. remaining incomplete items require genuinely unavailable:
   - hardware,
   - model weights,
   - operator terminal access,
   - exact-package external approval,
   - Creator Center/publication response;

AND

D. each remaining blocker has:
   - exact reason,
   - exact next command/action,
   - no fabricated status.

Continue until that point.
