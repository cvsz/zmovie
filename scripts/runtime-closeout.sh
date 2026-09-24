#!/usr/bin/env bash
set -Eeuo pipefail

# zMovie one-click production runtime closeout for the DBC host.
# Evidence-first: unsupported hardware or missing model/project prerequisites are
# reported as BLOCKED/PENDING and are never promoted to PASS.

REPO_DIR="${ZMOVIE_REPO_DIR:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)}"
INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
DATA_DIR="${ZMOVIE_DATA_DIR:-/var/lib/zmovie}"
CTL="${ZMOVIE_CTL:-/usr/local/bin/zmovie-ctl}"
PROJECT_ID="${ZMOVIE_CLOSEOUT_PROJECT_ID:-}"
PROVIDER="${ZMOVIE_CLOSEOUT_PROVIDER:-auto}"
DO_DEPLOY=1
DO_SERVICE_RESTART=1
DO_HOST_REBOOT=0
RESUME_MODE=0

usage() {
  cat <<'EOF'
Usage:
  sudo ./scripts/runtime-closeout.sh [options]

Options:
  --project ID        Project used for the real end-to-end production run.
  --provider ID       auto|sdcpp|comfyui|webhook (default: auto).
  --no-deploy         Skip git pull + native upgrade.
  --no-restart        Skip controlled web/worker restart verification.
  --reboot            Perform ONE controlled host reboot and auto-resume once.
  --resume            Internal resume mode used after --reboot.
  -h, --help          Show help.

Environment equivalents:
  ZMOVIE_CLOSEOUT_PROJECT_ID
  ZMOVIE_CLOSEOUT_PROVIDER
  ZMOVIE_REPO_DIR

DBC policy:
  NVIDIA GeForce 210 is treated as display-only. GPU/Vulkan/CUDA acceleration is
  NOT a success requirement on this host; CPU production is the expected mode.
EOF
}

while (($#)); do
  case "$1" in
    --project) PROJECT_ID="${2:?missing project id}"; shift 2 ;;
    --provider) PROVIDER="${2:?missing provider}"; shift 2 ;;
    --no-deploy) DO_DEPLOY=0; shift ;;
    --no-restart) DO_SERVICE_RESTART=0; shift ;;
    --reboot) DO_HOST_REBOOT=1; shift ;;
    --resume) RESUME_MODE=1; DO_DEPLOY=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ ${EUID} -eq 0 ]] || { echo "ERROR: run with sudo/root" >&2; exit 2; }
[[ "$PROVIDER" =~ ^(auto|sdcpp|comfyui|webhook)$ ]] || { echo "ERROR: invalid provider: $PROVIDER" >&2; exit 2; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT_ROOT="${ZMOVIE_CLOSEOUT_REPORT_ROOT:-$DATA_DIR/evidence/runtime-closeout}"
REPORT_DIR="$REPORT_ROOT/$STAMP"
mkdir -p "$REPORT_DIR"
chmod 0750 "$REPORT_ROOT" "$REPORT_DIR" || true
SUMMARY_TSV="$REPORT_DIR/summary.tsv"
: > "$SUMMARY_TSV"

log() { printf '[closeout] %s\n' "$*"; }
record() {
  local gate="$1" status="$2" detail="$3"
  detail="${detail//$'\t'/ }"
  detail="${detail//$'\n'/ }"
  printf '%s\t%s\t%s\n' "$gate" "$status" "$detail" >> "$SUMMARY_TSV"
  printf '[%-26s] %-8s %s\n' "$gate" "$status" "$detail"
}

run_capture() {
  local name="$1"; shift
  local out="$REPORT_DIR/${name}.log"
  set +e
  "$@" >"$out" 2>&1
  local rc=$?
  set -e
  printf '%s' "$rc"
}

json_pretty_or_raw() {
  local input="$1" output="$2"
  if python3 -m json.tool "$input" >"$output" 2>/dev/null; then
    return 0
  fi
  cp "$input" "$output"
  return 1
}

command_exists() { command -v "$1" >/dev/null 2>&1; }

# Hardware snapshot: this is evidence, not a gate that pretends GeForce 210 is ML-capable.
{
  echo "timestamp_utc=$STAMP"
  echo "hostname=$(hostname -f 2>/dev/null || hostname)"
  echo "kernel=$(uname -srmo)"
  echo "cpu=$(lscpu 2>/dev/null | awk -F: '/Model name/{gsub(/^[ \t]+/,"",$2); print $2; exit}')"
  echo "memory=$(free -h 2>/dev/null | awk '/Mem:/{print $2" total, "$7" available"}')"
  echo
  echo "--- PCI display devices ---"
  lspci -nn 2>/dev/null | grep -Ei 'vga|3d|display' || true
  echo
  echo "--- block devices ---"
  lsblk -e7 -o NAME,MODEL,SIZE,TYPE,FSTYPE,MOUNTPOINTS 2>/dev/null || true
  echo
  echo "--- filesystems ---"
  df -hT 2>/dev/null || true
} > "$REPORT_DIR/hardware.txt"

if grep -qi 'GeForce 210' "$REPORT_DIR/hardware.txt"; then
  record "hardware-policy" "PASS" "GeForce 210 detected and classified display-only; CPU rendering is expected"
else
  record "hardware-policy" "WARN" "GeForce 210 not detected in PCI snapshot; DBC policy still forbids assuming modern GPU acceleration"
fi

# Gate 1: deploy latest main and prove service health.
if ((DO_DEPLOY)) && ((RESUME_MODE == 0)); then
  log "Gate 1/5: deploy latest main"
  if [[ -d "$REPO_DIR/.git" ]]; then
    rc="$(run_capture git-fetch git -C "$REPO_DIR" fetch origin main)"
    if [[ "$rc" -eq 0 ]]; then
      local_head="$(git -C "$REPO_DIR" rev-parse HEAD 2>/dev/null || true)"
      remote_head="$(git -C "$REPO_DIR" rev-parse origin/main 2>/dev/null || true)"
      branch="$(git -C "$REPO_DIR" branch --show-current 2>/dev/null || true)"
      if [[ "$branch" == "main" && -n "$remote_head" && "$local_head" != "$remote_head" ]]; then
        rc="$(run_capture git-pull git -C "$REPO_DIR" pull --ff-only origin main)"
      fi
      if [[ "$branch" != "main" ]]; then
        record "deploy-latest-main" "BLOCKED" "repo is on branch '$branch'; refusing to switch a possibly dirty production checkout"
      elif [[ "$rc" -ne 0 ]]; then
        record "deploy-latest-main" "FAIL" "git fetch/pull failed; see git logs"
      else
        ready_rc="$(run_capture upgrade-readiness "$CTL" upgrade-readiness)"
        if [[ "$ready_rc" -ne 0 ]]; then
          record "deploy-latest-main" "BLOCKED" "upgrade-readiness refused deployment; active long-running work may exist"
        else
          up_rc="$(run_capture upgrade bash "$REPO_DIR/install.sh" upgrade)"
          if [[ "$up_rc" -eq 0 ]]; then
            record "deploy-latest-main" "PASS" "latest main upgraded successfully"
          else
            record "deploy-latest-main" "FAIL" "native upgrade failed; see upgrade.log"
          fi
        fi
      fi
    else
      record "deploy-latest-main" "FAIL" "git fetch origin main failed"
    fi
  else
    record "deploy-latest-main" "BLOCKED" "production repository checkout not found at $REPO_DIR"
  fi
else
  record "deploy-latest-main" "SKIP" "deployment skipped/resume mode"
fi

health_rc="$(run_capture health "$CTL" health)"
if [[ "$health_rc" -eq 0 ]]; then
  record "service-health" "PASS" "zMovie health endpoint passed"
else
  record "service-health" "FAIL" "zMovie health check failed"
fi

# Gate 2: durable restart/recovery. Full reboot is optional and resumes automatically.
if ((DO_SERVICE_RESTART)); then
  log "Gate 2/5: durable restart/recovery"
  before_rc="$(run_capture worker-before "$CTL" worker-status)"
  restart_rc="$(run_capture web-restart systemctl restart zmovie)"
  worker_rc="$(run_capture worker-restart systemctl restart zmovie-worker)"
  sleep 3
  after_health_rc="$(run_capture health-after-restart "$CTL" health)"
  after_worker_rc="$(run_capture worker-after "$CTL" worker-status)"
  if [[ "$before_rc" -eq 0 && "$restart_rc" -eq 0 && "$worker_rc" -eq 0 && "$after_health_rc" -eq 0 && "$after_worker_rc" -eq 0 ]]; then
    record "restart-recovery" "PASS" "web and durable worker restarted and recovered healthy"
  else
    record "restart-recovery" "FAIL" "restart/recovery check failed; inspect restart logs"
  fi
else
  record "restart-recovery" "SKIP" "controlled restart skipped"
fi

if ((DO_HOST_REBOOT)) && ((RESUME_MODE == 0)); then
  log "Scheduling one-time reboot resume"
  state_dir="/var/lib/zmovie/runtime-closeout-resume"
  mkdir -p "$state_dir"
  cat > "$state_dir/resume.env" <<EOF
PROJECT_ID=$(printf '%q' "$PROJECT_ID")
PROVIDER=$(printf '%q' "$PROVIDER")
REPO_DIR=$(printf '%q' "$REPO_DIR")
EOF
  cat > /etc/systemd/system/zmovie-runtime-closeout-resume.service <<EOF
[Unit]
Description=zMovie one-time runtime closeout resume
After=network-online.target zmovie.service zmovie-worker.service
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/bash -lc 'source $state_dir/resume.env; ZMOVIE_CLOSEOUT_PROJECT_ID="\$PROJECT_ID" ZMOVIE_CLOSEOUT_PROVIDER="\$PROVIDER" ZMOVIE_REPO_DIR="\$REPO_DIR" $INSTALL_DIR/scripts/runtime-closeout.sh --resume --no-deploy'
ExecStartPost=/bin/systemctl disable zmovie-runtime-closeout-resume.service

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable zmovie-runtime-closeout-resume.service
  cp "$SUMMARY_TSV" "$state_dir/pre-reboot-summary.tsv"
  sync
  log "Rebooting now; closeout will resume once after boot"
  systemctl reboot
  exit 0
fi

if ((RESUME_MODE)); then
  record "host-reboot" "PASS" "script resumed automatically after controlled host reboot"
else
  record "host-reboot" "PENDING" "full host reboot not requested; use --reboot for reboot-level evidence"
fi

# Gate 3: hardware and renderer policy. On DBC, CPU readiness is acceptable.
log "Gate 3/5: renderer/hardware policy"
renderer_rc="$(run_capture renderer-doctor "$CTL" renderer-doctor)"
sdcpp_rc="$(run_capture sdcpp-status "$CTL" sdcpp-status)"

selected="$PROVIDER"
if [[ "$selected" == "auto" ]]; then
  if [[ "$sdcpp_rc" -eq 0 ]] && grep -Eqi 'production_ready[^[:alnum:]]*(true|True)|"production_ready"[[:space:]]*:[[:space:]]*true' "$REPORT_DIR/sdcpp-status.log"; then
    selected="sdcpp"
  else
    providers_rc="$(run_capture providers "$CTL" providers)"
    if [[ "$providers_rc" -eq 0 ]] && grep -qi 'comfyui' "$REPORT_DIR/providers.log"; then
      selected="comfyui"
    else
      selected=""
    fi
  fi
fi
printf '%s\n' "$selected" > "$REPORT_DIR/selected-provider.txt"

if [[ "$renderer_rc" -eq 0 ]]; then
  record "renderer-diagnostics" "PASS" "renderer diagnostics completed; GeForce 210 acceleration is not required"
else
  record "renderer-diagnostics" "WARN" "renderer doctor reported limitations; CPU-only DBC policy may be expected"
fi

# Gate 4: factual real-model evidence. This does not auto-download huge model weights.
log "Gate 4/5: real-model evidence"
evidence_rc="$(run_capture sdcpp-evidence "$CTL" sdcpp-evidence --run-smoke)"
if [[ "$selected" == "sdcpp" ]]; then
  if [[ "$sdcpp_rc" -eq 0 && "$evidence_rc" -eq 0 ]] && grep -Eqi 'production_ready[^[:alnum:]]*(true|True)|"production_ready"[[:space:]]*:[[:space:]]*true' "$REPORT_DIR/sdcpp-status.log"; then
    record "real-model" "PASS" "stable-diffusion.cpp reports production-ready model configuration and evidence command passed"
  else
    record "real-model" "BLOCKED" "sdcpp is not real-model production-ready; configure compatible video weights first"
  fi
elif [[ "$selected" == "comfyui" ]]; then
  doctor_rc="$(run_capture production-doctor "$CTL" doctor)"
  if [[ "$doctor_rc" -eq 0 ]]; then
    record "real-model" "PASS" "ComfyUI production doctor passed; real output is still proven by Gate 5"
  else
    record "real-model" "BLOCKED" "ComfyUI production readiness failed"
  fi
else
  record "real-model" "BLOCKED" "no production-capable provider selected/configured"
fi

# Gate 5: end-to-end real production run. Existing production command validates media,
# assembles final output, prepares the package, and exports checksums; it stops before
# external Bilibili publication/approval.
log "Gate 5/5: end-to-end production acceptance"
if [[ -z "$PROJECT_ID" ]]; then
  record "n2n-production" "PENDING" "set --project ID or ZMOVIE_CLOSEOUT_PROJECT_ID to run real production acceptance"
elif [[ -z "$selected" ]]; then
  record "n2n-production" "BLOCKED" "no production-capable provider available"
else
  prod_rc="$(run_capture production "$CTL" production "$PROJECT_ID" "$selected")"
  status_rc="$(run_capture run-status "$CTL" run-status "$PROJECT_ID")"
  if [[ "$prod_rc" -eq 0 && "$status_rc" -eq 0 ]] && ! grep -Eqi '"status"[[:space:]]*:[[:space:]]*"failed"|error|traceback' "$REPORT_DIR/production.log"; then
    record "n2n-production" "PASS" "production pipeline completed for $PROJECT_ID with provider=$selected"
  else
    record "n2n-production" "FAIL" "production acceptance failed or incomplete for $PROJECT_ID; inspect production.log/run-status.log"
  fi
fi

# Generate machine-readable + human-readable reports without leaking environment secrets.
python3 - "$SUMMARY_TSV" "$REPORT_DIR/report.json" "$REPORT_DIR/report.md" "$STAMP" "$PROJECT_ID" "$selected" <<'PY'
import json, pathlib, sys
summary, jout, mout, stamp, project, provider = sys.argv[1:]
rows=[]
for line in pathlib.Path(summary).read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    gate,status,detail=(line.split('\t',2)+['',''])[:3]
    rows.append({'gate':gate,'status':status,'detail':detail})
blocking={'FAIL','BLOCKED','PENDING'}
overall='PASS' if rows and not any(r['status'] in blocking for r in rows) else 'INCOMPLETE'
payload={
    'schema':'zmovie.runtime-closeout.v1',
    'timestamp_utc':stamp,
    'project_id':project or None,
    'provider':provider or None,
    'overall':overall,
    'dbc_policy':{
        'geforce_210':'display-only',
        'expected_render_mode':'CPU-only',
        'gpu_acceleration_required':False,
    },
    'checks':rows,
}
pathlib.Path(jout).write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
md=['# zMovie DBC Runtime Closeout','',f'- Timestamp UTC: `{stamp}`',f'- Overall: **{overall}**',f'- Project: `{project or "not supplied"}`',f'- Provider: `{provider or "none"}`','',
    '> DBC hardware policy: GeForce 210 is display-only. CPU-only production is expected; CUDA/Vulkan ML acceleration is not a completion requirement.','',
    '| Gate | Status | Evidence |','|---|---|---|']
for r in rows:
    detail=r['detail'].replace('|','\\|')
    md.append(f"| {r['gate']} | **{r['status']}** | {detail} |")
md += ['', '## Evidence files', '', 'All command outputs for this run are stored beside this report. No environment/secrets dump is collected.']
pathlib.Path(mout).write_text('\n'.join(md)+'\n',encoding='utf-8')
print(overall)
PY

overall="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["overall"])' "$REPORT_DIR/report.json")"
log "Report JSON: $REPORT_DIR/report.json"
log "Report Markdown: $REPORT_DIR/report.md"
cat "$REPORT_DIR/report.md"

if [[ "$overall" == "PASS" ]]; then
  exit 0
fi
exit 3
