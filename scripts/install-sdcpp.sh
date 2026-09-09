#!/usr/bin/env bash
set -Eeuo pipefail

BACKEND="${1:-auto}"
INSTALL_DIR="${SDCPP_INSTALL_DIR:-/opt/stable-diffusion.cpp}"
SOURCE_URL="${SDCPP_SOURCE_URL:-https://github.com/leejet/stable-diffusion.cpp}"
SOURCE_REF="${SDCPP_REF:-master}"
ENV_FILE="${ZMOVIE_ENV:-/etc/zmovie/zmovie.env}"
BUILD_JOBS="${SDCPP_BUILD_JOBS:-$(nproc)}"

log(){ printf '[zMovie sdcpp] %s\n' "$*"; }
fail(){ printf '[zMovie sdcpp] ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || fail "run this installer with sudo/root"
case "$BACKEND" in
  auto|vulkan|cpu) ;;
  *) fail "backend must be auto, vulkan, or cpu" ;;
esac
[[ "$BUILD_JOBS" =~ ^[1-9][0-9]*$ ]] || fail "SDCPP_BUILD_JOBS must be a positive integer"

export DEBIAN_FRONTEND=noninteractive
packages=(build-essential cmake git pkg-config)
if [[ "$BACKEND" != "cpu" ]]; then
  packages+=(libvulkan-dev glslc spirv-headers mesa-vulkan-drivers vulkan-tools)
fi
log "installing build/runtime packages"
apt-get update
apt-get install -y "${packages[@]}"

if [[ -d "$INSTALL_DIR/.git" ]]; then
  log "updating managed source checkout"
  git -C "$INSTALL_DIR" remote set-url origin "$SOURCE_URL"
  git -C "$INSTALL_DIR" fetch --depth=1 origin "$SOURCE_REF"
  git -C "$INSTALL_DIR" checkout --detach FETCH_HEAD
  git -C "$INSTALL_DIR" submodule sync --recursive
  git -C "$INSTALL_DIR" submodule update --init --recursive --depth=1
elif [[ -e "$INSTALL_DIR" ]]; then
  fail "$INSTALL_DIR exists but is not a managed stable-diffusion.cpp checkout"
else
  log "cloning stable-diffusion.cpp"
  git clone --recursive "$SOURCE_URL" "$INSTALL_DIR"
  git -C "$INSTALL_DIR" fetch --depth=1 origin "$SOURCE_REF"
  git -C "$INSTALL_DIR" checkout --detach FETCH_HEAD
  git -C "$INSTALL_DIR" submodule sync --recursive
  git -C "$INSTALL_DIR" submodule update --init --recursive --depth=1
fi

build_engine(){
  local mode="$1"
  rm -rf "$INSTALL_DIR/build"
  local -a args=(-S "$INSTALL_DIR" -B "$INSTALL_DIR/build" -DCMAKE_BUILD_TYPE=Release)
  if [[ "$mode" == "vulkan" ]]; then
    args+=(-DSD_VULKAN=ON)
  else
    args+=(-DSD_VULKAN=OFF)
  fi
  cmake "${args[@]}"
  cmake --build "$INSTALL_DIR/build" --config Release -j "$BUILD_JOBS"
}

BUILT_BACKEND="cpu"
if [[ "$BACKEND" == "cpu" ]]; then
  log "building CPU backend"
  build_engine cpu
else
  log "building Vulkan + CPU backend"
  if build_engine vulkan; then
    BUILT_BACKEND="vulkan"
  elif [[ "$BACKEND" == "auto" ]]; then
    log "Vulkan build failed; retrying CPU-only build"
    build_engine cpu
    BUILT_BACKEND="cpu"
  else
    fail "Vulkan build failed"
  fi
fi

SD_CLI=""
for candidate in \
  "$INSTALL_DIR/build/bin/sd-cli" \
  "$INSTALL_DIR/build/bin/Release/sd-cli" \
  "$INSTALL_DIR/build/sd-cli"; do
  if [[ -x "$candidate" ]]; then
    SD_CLI="$candidate"
    break
  fi
done
[[ -n "$SD_CLI" ]] || fail "sd-cli binary was not produced by the build"
install -m 0755 "$SD_CLI" /usr/local/bin/sd-cli
printf '%s\n' "$BUILT_BACKEND" > "$INSTALL_DIR/.zmovie-backend"

set_env(){
  local key="$1" value="$2" tmp found=0
  install -d -m 0755 "$(dirname "$ENV_FILE")"
  touch "$ENV_FILE"
  tmp="$(mktemp)"
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" == "$key="* ]]; then
      printf '%s=%s\n' "$key" "$value" >> "$tmp"
      found=1
    else
      printf '%s\n' "$line" >> "$tmp"
    fi
  done < "$ENV_FILE"
  if [[ "$found" -eq 0 ]]; then
    printf '%s=%s\n' "$key" "$value" >> "$tmp"
  fi
  cat "$tmp" > "$ENV_FILE"
  rm -f "$tmp"
}

set_env ZMOVIE_SDCPP_CLI /usr/local/bin/sd-cli
if [[ "$BACKEND" == "vulkan" ]]; then
  set_env ZMOVIE_SDCPP_BACKEND vulkan0
elif [[ "$BUILT_BACKEND" == "cpu" ]]; then
  set_env ZMOVIE_SDCPP_BACKEND cpu
else
  # stable-diffusion.cpp auto prefers a GPU/integrated GPU and falls back to CPU.
  set_env ZMOVIE_SDCPP_BACKEND auto
fi

if systemctl list-unit-files zmovie.service >/dev/null 2>&1; then
  systemctl try-restart zmovie.service || true
fi

log "installed /usr/local/bin/sd-cli (build backend: $BUILT_BACKEND)"
log "available stable-diffusion.cpp devices:"
/usr/local/bin/sd-cli --list-devices 2>&1 || true
log "no model weights were downloaded"
log "next: configure a video-capable model bundle with scripts/configure-sdcpp.sh"
