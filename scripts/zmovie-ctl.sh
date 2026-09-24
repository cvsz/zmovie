#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
DATA_DIR="${ZMOVIE_DATA_DIR:-/var/lib/zmovie}"
ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
SERVICE_NAME="${ZMOVIE_SERVICE_NAME:-zmovie}"
WORKER_SERVICE_NAME="${ZMOVIE_WORKER_SERVICE_NAME:-zmovie-worker}"
PYTHON_BIN="${INSTALL_DIR}/.venv/bin/python"
PUBLIC_BASE_URL="${ZMOVIE_PUBLIC_BASE_URL:-https://zmovie.zeaz.dev}"
COMMAND="${1:-menu}"

log(){ printf '[zMovie ctl] %s\n' "$*"; }
fail(){ printf '[zMovie ctl] ERROR: %s\n' "$*" >&2; exit 1; }
need_root(){ [[ ${EUID} -eq 0 ]] || fail "this command requires root; rerun with sudo"; }

require_install(){
  [[ -d "$INSTALL_DIR" ]] || fail "install directory not found: $INSTALL_DIR"
  [[ -f "$ENV_FILE" ]] || fail "environment file not found: $ENV_FILE"
  [[ -x "$PYTHON_BIN" ]] || fail "Python runtime not found: $PYTHON_BIN"
}

as_service(){
  require_install
  if [[ "$(id -un)" == "$SERVICE_USER" ]]; then
    env HOME="$DATA_DIR" bash --noprofile --norc -c \
      'set -Eeuo pipefail; set -a; source "$1"; set +a; cd "$2"; shift 2; exec "$@"' \
      _ "$ENV_FILE" "$INSTALL_DIR" "$@"
  elif [[ ${EUID} -eq 0 ]]; then
    runuser -u "$SERVICE_USER" -- env HOME="$DATA_DIR" bash --noprofile --norc -c \
      'set -Eeuo pipefail; set -a; source "$1"; set +a; cd "$2"; shift 2; exec "$@"' \
      _ "$ENV_FILE" "$INSTALL_DIR" "$@"
  else
    sudo -u "$SERVICE_USER" env HOME="$DATA_DIR" bash --noprofile --norc -c \
      'set -Eeuo pipefail; set -a; source "$1"; set +a; cd "$2"; shift 2; exec "$@"' \
      _ "$ENV_FILE" "$INSTALL_DIR" "$@"
  fi
}

app(){ as_service "$PYTHON_BIN" -m zmovie_platform.control_cli "$@"; }
runtime(){ as_service "$PYTHON_BIN" -m zmovie_platform.runtime_ops "$@"; }

port(){
  local value
  value="$(sed -n 's/^ZMOVIE_PORT=//p' "$ENV_FILE" 2>/dev/null | tail -n1 || true)"
  printf '%s' "${value:-8080}"
}

health(){
  require_install
  curl -fsS --max-time 10 "http://127.0.0.1:$(port)/api/v2/health" | python3 -m json.tool
}

status(){
  systemctl --no-pager --full status "$SERVICE_NAME" || true
  printf '\n--- worker ---\n'
  systemctl --no-pager --full status "$WORKER_SERVICE_NAME" || true
  printf '\n--- health ---\n'
  health || true
}

logs(){
  local service="$1"
  local lines="${2:-100}"
  [[ "$lines" =~ ^[0-9]+$ ]] || fail "logs line count must be numeric"
  journalctl -u "$service" -n "$lines" --no-pager
}

config_redacted(){
  require_install
  awk -F= '
    /^[[:space:]]*#/ || NF < 2 { print; next }
    {
      key=$1
      upper=toupper(key)
      if (upper ~ /(PASSWORD|SECRET|TOKEN|KEY|COOKIE|AUTH)/) {
        print key "=<redacted>"
      } else {
        print
      }
    }
  ' "$ENV_FILE"
}

doctor(){
  require_install
  local comfy_url
  comfy_url="$(sed -n 's/^ZMOVIE_COMFYUI_URL=//p' "$ENV_FILE" | tail -n1)"
  comfy_url="${comfy_url#\'}"
  comfy_url="${comfy_url%\'}"
  ZMOVIE_URL="http://127.0.0.1:$(port)" \
  ZMOVIE_COMFYUI_URL="${comfy_url:-http://127.0.0.1:8188}" \
    bash "$INSTALL_DIR/scripts/doctor.sh"
}

usage(){
  cat <<'EOF'
zMovie full-stack control panel

Usage:
  zmovie-ctl [command] [arguments]

Service / installation:
  menu                         interactive control panel
  status                       systemd status + health
  health                       health JSON
  doctor                       zMovie + renderer production doctor
  logs [LINES]                 web service logs (default 100)
  start | stop | restart       manage web service (root)
  backup                       verified SQLite backup
  backups                      list verified backups
  backup-status                backup retention/status
  upgrade-readiness            fail-closed long-job upgrade gate
  upgrade                      upgrade from configured repository/ref (root)
  config                       print redacted runtime configuration
  studio                       print Studio URL

Durable worker:
  worker-status                queue summary + pause state
  worker-jobs                  list durable jobs
  worker-job ID                show one durable job
  worker-recover --dry-run     inspect stale leases
  worker-recover --apply       recover stale leases
  worker-pause                 pause new claims
  worker-resume                resume claims
  worker-restart               restart worker service (root)
  worker-logs [LINES]          worker journal

24/7 operations:
  watchdog-status              inspect health/watchdog inputs
  watchdog-run                 run conservative watchdog check
  renderer-doctor              /dev/dri + Vulkan + sd-cli diagnostics
  vulkan-status                same worker-side device diagnostic

Local stable-diffusion.cpp:
  sdcpp-status                 CPU/Vulkan engine + model production readiness
  sdcpp-install [BACKEND]      install/update engine; auto|vulkan|cpu (root)
  sdcpp-config OPTIONS...      configure video model bundle (root)
  sdcpp-evidence [--run-smoke] record factual runtime evidence

Production data plane:
  providers                    list configured render providers
  projects                     list projects
  hyperframes [--query TEXT] [--category CATEGORY]
  readiness PROJECT_ID         strict production readiness
  content --topic TEXT [--template TEMPLATE_ID] [...]
  render PROJECT_ID PROVIDER   enqueue real production render; mock rejected
  assemble PROJECT_ID          strict final assembly
  prepare PROJECT_ID           prepare Bilibili package from validated final
  export PROJECT_ID            build production ZIP + checksums
  production PROJECT_ID PROVIDER
                               enqueue render -> validate -> assemble -> prepare -> export
                               and STOP at human approval gate
  run-status PROJECT_ID [RUN]  production run + worker status

Bilibili control gates:
  bili-session                 live Bilibili session check
  bili-status JOB_ID           publish job state
  bili-approve JOB_ID APPROVE  record exact-package human approval
  bili-publish JOB_ID CONFIRM-PUBLISH
                               preflight + ONE real external submission

Important: submitted is not published. Public completion still requires a confirmed
Bilibili public URL and remote_confirmation=true.
EOF
}

menu(){
  [[ -t 0 ]] || { usage; return; }
  while true; do
    cat <<'EOF'

=== zMovie Control Panel ===
 1) Status + health
 2) Production doctor
 3) Providers
 4) Projects
 5) Production readiness
 6) Run one-click production package
 7) Bilibili session
 8) Bilibili job status
 9) Web service logs
10) Backup database
11) Restart web service
12) Upgrade full stack
13) Show redacted config
14) Hyperframes templates
15) stable-diffusion.cpp status
16) Install/update stable-diffusion.cpp (auto CPU/Vulkan)
17) Worker status
18) Worker jobs
19) Worker logs
20) Renderer/Vulkan doctor
21) Watchdog status
22) Backup status
23) Upgrade readiness
 0) Exit
EOF
    read -r -p 'Select: ' choice
    case "$choice" in
      1) status ;;
      2) doctor ;;
      3) app providers ;;
      4) app projects ;;
      5) read -r -p 'Project ID: ' project_id; app readiness "$project_id" ;;
      6) read -r -p 'Project ID: ' project_id; read -r -p 'Provider (comfyui/sdcpp/webhook): ' provider_id; app production "$project_id" --provider "$provider_id" ;;
      7) app bili-session ;;
      8) read -r -p 'Publish job ID: ' job_id; app bili-status "$job_id" ;;
      9) logs "$SERVICE_NAME" 100 ;;
      10) runtime backup ;;
      11) need_root; systemctl restart "$SERVICE_NAME"; status ;;
      12) need_root; runtime upgrade-readiness; bash "$INSTALL_DIR/install.sh" upgrade ;;
      13) config_redacted ;;
      14) app hyperframes ;;
      15) app sdcpp-status ;;
      16) need_root; bash "$INSTALL_DIR/scripts/install-sdcpp.sh" auto ;;
      17) runtime worker-status ;;
      18) runtime worker-jobs ;;
      19) logs "$WORKER_SERVICE_NAME" 100 ;;
      20) runtime renderer-doctor ;;
      21) runtime watchdog-status ;;
      22) runtime backup-status ;;
      23) runtime upgrade-readiness ;;
      0) return ;;
      *) log "unknown selection" ;;
    esac
  done
}

shift || true
case "$COMMAND" in
  menu) menu ;;
  help|-h|--help) usage ;;
  status) status ;;
  health) health ;;
  doctor) doctor ;;
  logs) logs "$SERVICE_NAME" "${1:-100}" ;;
  start) need_root; systemctl start "$SERVICE_NAME" ;;
  stop) need_root; systemctl stop "$SERVICE_NAME" ;;
  restart) need_root; systemctl restart "$SERVICE_NAME"; status ;;
  backup) runtime backup ;;
  backups) runtime backups ;;
  backup-status) runtime backup-status ;;
  upgrade-readiness) runtime upgrade-readiness ;;
  upgrade) need_root; require_install; runtime upgrade-readiness; bash "$INSTALL_DIR/install.sh" upgrade ;;
  config) config_redacted ;;
  studio) printf '%s/studio\n' "${PUBLIC_BASE_URL%/}" ;;
  worker-status) runtime worker-status ;;
  worker-jobs) runtime worker-jobs "$@" ;;
  worker-job) [[ $# -eq 1 ]] || fail "usage: zmovie-ctl worker-job ID"; runtime worker-job "$1" ;;
  worker-recover)
    if [[ "${1:-}" == "--apply" ]]; then runtime worker-recover --apply; else runtime worker-recover; fi
    ;;
  worker-pause) runtime worker-pause ;;
  worker-resume) runtime worker-resume ;;
  worker-restart) need_root; systemctl restart "$WORKER_SERVICE_NAME"; runtime worker-status ;;
  worker-logs) logs "$WORKER_SERVICE_NAME" "${1:-100}" ;;
  watchdog-status) runtime watchdog-status ;;
  watchdog-run) runtime watchdog-run ;;
  renderer-doctor) runtime renderer-doctor ;;
  vulkan-status) runtime vulkan-status ;;
  sdcpp-evidence) runtime sdcpp-evidence "$@" ;;
  sdcpp-status) app sdcpp-status ;;
  sdcpp-install)
    need_root
    require_install
    backend="${1:-auto}"
    [[ "$backend" =~ ^(auto|vulkan|cpu)$ ]] || fail "usage: zmovie-ctl sdcpp-install [auto|vulkan|cpu]"
    bash "$INSTALL_DIR/scripts/install-sdcpp.sh" "$backend"
    ;;
  sdcpp-config) need_root; require_install; bash "$INSTALL_DIR/scripts/configure-sdcpp.sh" "$@" ;;
  providers) app providers ;;
  projects) app projects ;;
  hyperframes) app hyperframes "$@" ;;
  readiness) [[ $# -eq 1 ]] || fail "usage: zmovie-ctl readiness PROJECT_ID"; app readiness "$1" ;;
  content) app content "$@" ;;
  render) [[ $# -eq 2 ]] || fail "usage: zmovie-ctl render PROJECT_ID PROVIDER"; app render "$1" --provider "$2" ;;
  assemble) [[ $# -eq 1 ]] || fail "usage: zmovie-ctl assemble PROJECT_ID"; app assemble "$1" ;;
  prepare) [[ $# -eq 1 ]] || fail "usage: zmovie-ctl prepare PROJECT_ID"; app prepare-bilibili "$1" ;;
  export) [[ $# -eq 1 ]] || fail "usage: zmovie-ctl export PROJECT_ID"; app export "$1" ;;
  production) [[ $# -eq 2 ]] || fail "usage: zmovie-ctl production PROJECT_ID PROVIDER"; app production "$1" --provider "$2" ;;
  run-status)
    [[ $# -ge 1 && $# -le 2 ]] || fail "usage: zmovie-ctl run-status PROJECT_ID [RUN_ID]"
    if [[ $# -eq 2 ]]; then app run-status "$1" --run-id "$2"; else app run-status "$1"; fi
    ;;
  bili-session) app bili-session ;;
  bili-status) [[ $# -eq 1 ]] || fail "usage: zmovie-ctl bili-status JOB_ID"; app bili-status "$1" ;;
  bili-approve) [[ $# -eq 2 && "$2" == "APPROVE" ]] || fail "usage: zmovie-ctl bili-approve JOB_ID APPROVE"; app bili-approve "$1" --confirm "$2" ;;
  bili-publish) [[ $# -eq 2 && "$2" == "CONFIRM-PUBLISH" ]] || fail "usage: zmovie-ctl bili-publish JOB_ID CONFIRM-PUBLISH"; app bili-publish "$1" --confirm "$2" ;;
  *) fail "unknown command: $COMMAND (run 'zmovie-ctl help')" ;;
esac
