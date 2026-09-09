#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
CLI="${ZMOVIE_SDCPP_CLI:-/usr/local/bin/sd-cli}"
BACKEND="auto"
MODEL=""
DIFFUSION_MODEL=""
HIGH_NOISE_DIFFUSION_MODEL=""
VAE=""
AUDIO_VAE=""
T5XXL=""
LLM=""
CLIP_VISION=""
EMBEDDINGS_CONNECTORS=""
PARAMS_BACKEND=""
MAX_VRAM=""
EXTRA_ARGS_JSON=""
FPS="8"
OUTPUT_FORMAT="avi"

log(){ printf '[zMovie sdcpp config] %s\n' "$*"; }
fail(){ printf '[zMovie sdcpp config] ERROR: %s\n' "$*" >&2; exit 1; }
usage(){
  cat <<'EOF'
Usage:
  sudo bash scripts/configure-sdcpp.sh [options]

Required on each configuration run:
  --model PATH                 monolithic model/checkpoint, OR
  --diffusion-model PATH       standalone diffusion/video model

Common video bundle options:
  --vae PATH
  --t5xxl PATH
  --llm PATH
  --audio-vae PATH
  --high-noise-diffusion-model PATH
  --clip-vision PATH
  --embeddings-connectors PATH

Runtime options:
  --backend auto|cpu|gpu|vulkan0   default: auto
  --params-backend VALUE
  --max-vram VALUE
  --fps N                           default: 8
  --output-format avi|webm         default: avi
  --extra-args-json JSON           e.g. '["--steps","8","--cfg-scale","6"]'

The script never downloads model weights. It validates configured files and
explicitly enables the sdcpp video provider. Real outputs must still pass the
zMovie ffprobe production-media gate.
EOF
}

[[ ${EUID} -eq 0 ]] || fail "run with sudo/root"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model) MODEL="${2:-}"; shift 2 ;;
    --diffusion-model) DIFFUSION_MODEL="${2:-}"; shift 2 ;;
    --high-noise-diffusion-model) HIGH_NOISE_DIFFUSION_MODEL="${2:-}"; shift 2 ;;
    --vae) VAE="${2:-}"; shift 2 ;;
    --audio-vae) AUDIO_VAE="${2:-}"; shift 2 ;;
    --t5xxl) T5XXL="${2:-}"; shift 2 ;;
    --llm) LLM="${2:-}"; shift 2 ;;
    --clip-vision) CLIP_VISION="${2:-}"; shift 2 ;;
    --embeddings-connectors) EMBEDDINGS_CONNECTORS="${2:-}"; shift 2 ;;
    --backend) BACKEND="${2:-}"; shift 2 ;;
    --params-backend) PARAMS_BACKEND="${2:-}"; shift 2 ;;
    --max-vram) MAX_VRAM="${2:-}"; shift 2 ;;
    --fps) FPS="${2:-}"; shift 2 ;;
    --output-format) OUTPUT_FORMAT="${2:-}"; shift 2 ;;
    --extra-args-json) EXTRA_ARGS_JSON="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) fail "unknown option: $1" ;;
  esac
done

[[ -x "$CLI" ]] || fail "sd-cli is not executable: $CLI; run scripts/install-sdcpp.sh first"
[[ -n "$MODEL" || -n "$DIFFUSION_MODEL" ]] || fail "provide --model or --diffusion-model"
case "$BACKEND" in
  auto|cpu|gpu|vulkan[0-9]*|cuda[0-9]*|metal|sycl[0-9]*) ;;
  *) fail "unsupported backend: $BACKEND" ;;
esac
[[ "$FPS" =~ ^[1-9][0-9]*$ ]] || fail "--fps must be a positive integer"
(( FPS <= 60 )) || fail "--fps must be <= 60"
case "$OUTPUT_FORMAT" in avi|webm) ;; *) fail "--output-format must be avi or webm" ;; esac

validate_value(){
  local value="$1"
  [[ "$value" != *$'\n'* && "$value" != *$'\r'* ]] || fail "configuration values cannot contain newlines"
  [[ "$value" != *"'"* ]] || fail "configuration values cannot contain single quotes"
}

check_model(){
  local label="$1" path="$2"
  [[ -n "$path" ]] || return 0
  validate_value "$path"
  [[ -f "$path" ]] || fail "$label not found: $path"
  if id "$SERVICE_USER" >/dev/null 2>&1; then
    runuser -u "$SERVICE_USER" -- test -r "$path" || fail "$label is not readable by service user $SERVICE_USER: $path"
  fi
}

check_model model "$MODEL"
check_model diffusion_model "$DIFFUSION_MODEL"
check_model high_noise_diffusion_model "$HIGH_NOISE_DIFFUSION_MODEL"
check_model vae "$VAE"
check_model audio_vae "$AUDIO_VAE"
check_model t5xxl "$T5XXL"
check_model llm "$LLM"
check_model clip_vision "$CLIP_VISION"
check_model embeddings_connectors "$EMBEDDINGS_CONNECTORS"
validate_value "$BACKEND"
validate_value "$PARAMS_BACKEND"
validate_value "$MAX_VRAM"

if [[ -n "$EXTRA_ARGS_JSON" ]]; then
  validate_value "$EXTRA_ARGS_JSON"
  python3 - "$EXTRA_ARGS_JSON" <<'PY'
import json
import sys
value = json.loads(sys.argv[1])
if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise SystemExit("--extra-args-json must be a non-empty JSON array of strings")
PY
fi

set_env(){
  local key="$1" value="$2" tmp found=0
  validate_value "$value"
  install -d -m 0755 "$(dirname "$ENV_FILE")"
  touch "$ENV_FILE"
  tmp="$(mktemp)"
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" == "$key="* ]]; then
      printf "%s='%s'\n" "$key" "$value" >> "$tmp"
      found=1
    else
      printf '%s\n' "$line" >> "$tmp"
    fi
  done < "$ENV_FILE"
  if [[ "$found" -eq 0 ]]; then
    printf "%s='%s'\n" "$key" "$value" >> "$tmp"
  fi
  cat "$tmp" > "$ENV_FILE"
  rm -f "$tmp"
}

set_if_present(){
  local key="$1" value="$2"
  [[ -n "$value" ]] || return 0
  set_env "$key" "$value"
}

set_env ZMOVIE_SDCPP_CLI "$CLI"
set_env ZMOVIE_SDCPP_BACKEND "$BACKEND"
set_env ZMOVIE_SDCPP_VIDEO_ENABLED true
set_env ZMOVIE_SDCPP_FPS "$FPS"
set_env ZMOVIE_SDCPP_OUTPUT_FORMAT "$OUTPUT_FORMAT"
set_if_present ZMOVIE_SDCPP_MODEL "$MODEL"
set_if_present ZMOVIE_SDCPP_DIFFUSION_MODEL "$DIFFUSION_MODEL"
set_if_present ZMOVIE_SDCPP_HIGH_NOISE_DIFFUSION_MODEL "$HIGH_NOISE_DIFFUSION_MODEL"
set_if_present ZMOVIE_SDCPP_VAE "$VAE"
set_if_present ZMOVIE_SDCPP_AUDIO_VAE "$AUDIO_VAE"
set_if_present ZMOVIE_SDCPP_T5XXL "$T5XXL"
set_if_present ZMOVIE_SDCPP_LLM "$LLM"
set_if_present ZMOVIE_SDCPP_CLIP_VISION "$CLIP_VISION"
set_if_present ZMOVIE_SDCPP_EMBEDDINGS_CONNECTORS "$EMBEDDINGS_CONNECTORS"
set_if_present ZMOVIE_SDCPP_PARAMS_BACKEND "$PARAMS_BACKEND"
set_if_present ZMOVIE_SDCPP_MAX_VRAM "$MAX_VRAM"
set_if_present ZMOVIE_SDCPP_EXTRA_ARGS_JSON "$EXTRA_ARGS_JSON"

if systemctl list-unit-files zmovie.service >/dev/null 2>&1; then
  systemctl try-restart zmovie.service || true
fi

log "configuration saved; video mode explicitly enabled"
log "backend=$BACKEND fps=$FPS output_format=$OUTPUT_FORMAT"
log "probing available devices"
"$CLI" --list-devices 2>&1 || true
log "next: sudo zmovie-ctl sdcpp-status"
