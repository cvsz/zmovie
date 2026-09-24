# DBC one-click runtime closeout

`./scripts/runtime-closeout.sh` is the evidence-first acceptance runner for the five remaining production-runtime gates on the DBC server.

The runner is aligned with `docs/server-spec.md`: Dell PowerEdge T30 / Xeon E3-1225 v5, 32GB RAM, Samsung 870 QVO SSD, HDD storage, and NVIDIA GeForce 210. The GeForce 210 is treated as **display-only**. CUDA/Vulkan ML acceleration is therefore **not** a completion requirement; CPU rendering is the expected local mode.

## What one run verifies

1. Fetch/pull latest `main`, run the fail-closed upgrade-readiness gate, and perform the native upgrade.
2. Verify the web service and durable worker across controlled service restarts. `--reboot` additionally installs a one-time systemd resume unit, reboots once, and continues the closeout automatically after boot.
3. Capture CPU/RAM/GPU/storage evidence and run renderer diagnostics under the DBC CPU-only policy.
4. Run factual stable-diffusion.cpp/model evidence checks without downloading or fabricating model weights. Missing compatible video weights remain `BLOCKED`.
5. Run the existing production pipeline for a supplied project: real render provider -> media validation -> assembly -> package preparation -> export. External Bilibili publication remains outside this closeout and still requires its explicit approval/confirmation gates.

## One command

From a production checkout:

```bash
sudo ./scripts/runtime-closeout.sh \
  --project prj_YOUR_REAL_PROJECT \
  --provider auto
```

For reboot-level recovery evidence in the same operation:

```bash
sudo ./scripts/runtime-closeout.sh \
  --project prj_YOUR_REAL_PROJECT \
  --provider auto \
  --reboot
```

The script reboots only when `--reboot` is explicitly supplied. It creates a one-time `zmovie-runtime-closeout-resume.service`, resumes automatically after boot, and disables that unit after the resumed run.

Environment form:

```bash
sudo env \
  ZMOVIE_CLOSEOUT_PROJECT_ID=prj_YOUR_REAL_PROJECT \
  ZMOVIE_CLOSEOUT_PROVIDER=auto \
  ./scripts/runtime-closeout.sh
```

## Reports

Each run writes a timestamped evidence directory below:

```text
/var/lib/zmovie/evidence/runtime-closeout/YYYYMMDDTHHMMSSZ/
```

Primary outputs:

- `report.json` — machine-readable `zmovie.runtime-closeout.v1` report.
- `report.md` — operator-readable completion table.
- `hardware.txt` — CPU, RAM, PCI display devices, block devices, and filesystem capacity.
- individual `*.log` files — command evidence for deployment, health, restart, renderer/model checks, production and run status.

The report uses `PASS`, `WARN`, `SKIP`, `PENDING`, `BLOCKED`, and `FAIL`. Overall status is `PASS` only when no `FAIL`, `BLOCKED`, or `PENDING` gate remains. A missing model or missing project ID never becomes a false success.

## DBC hardware interpretation

Per `docs/server-spec.md`:

- Xeon E3-1225 v5 is the expected compute engine for local rendering/inference.
- 32GB RAM is sufficient for the combined service within conservative CPU-only allocations, subject to the actual model's memory needs.
- GeForce 210 1GB DDR3 cannot provide modern CUDA/TensorRT/Vulkan-ML acceleration and is display-only.
- The Samsung SSD should host the VM/database/hot zMovie data; HDDs are appropriate for bulk media/backups according to operator mount policy.
- `hardware.txt` records the *actual* runtime disks/mounts rather than assuming the documentation still matches the installed drives.

## Exit codes

- `0`: all closeout gates in this run passed.
- `2`: invalid invocation/precondition.
- `3`: report generated, but one or more required gates are incomplete, blocked, pending or failed.

This runner does not publish externally and does not download large model weights automatically.
