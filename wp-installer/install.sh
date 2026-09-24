#!/usr/bin/env bash
set -Eeuo pipefail

INSTALLER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_DIR="$(cd -- "$INSTALLER_DIR/.." && pwd -P)"
ENV_FILE="$INSTALLER_DIR/.env"
COMPOSE_FILE="$INSTALLER_DIR/compose.yaml"

usage() {
    cat <<'HELP'
Usage: bash wp-installer/install.sh [install|status|stop|--dry-run|--help]
  install     Download and install WordPress + ZeaZ Cinema on local Docker staging.
  status      Show WordPress and MariaDB containers.
  stop        Stop this staging stack without deleting its volumes.
  --dry-run   Show the installation steps without changing files or starting Docker.
  --help      Show this message.

Configuration: wp-installer/.env (generated on first real install; gitignored).
Secrets are generated automatically and are never printed by this script.
HELP
}

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

check_sources() {
    [[ -s "$REPO_DIR/wp-plugins/zwp-cinema/zwp-cinema.php" ]] || die 'Missing ZeaZ Cinema plugin source.'
    [[ -s "$REPO_DIR/themes/zwp-cinema/style.css" ]] || die 'Missing ZeaZ Cinema theme source.'
    [[ -s "$REPO_DIR/themes/zwp-cinema/index.php" ]] || die 'Missing ZeaZ Cinema theme template.'
    [[ -s "$INSTALLER_DIR/scripts/bootstrap.sh" ]] || die 'Missing WP-CLI bootstrap script.'
}

make_secret() {
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -hex 32
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c 'import secrets; print(secrets.token_hex(32))'
    else
        die 'Install openssl or python3 to securely generate secrets.'
    fi
}

ensure_env() {
    if [[ ! -e "$ENV_FILE" ]]; then
        umask 077
        cp "$INSTALLER_DIR/.env.example" "$ENV_FILE"
        printf 'Created private configuration: %s\n' "$ENV_FILE"
    fi
    chmod 600 "$ENV_FILE"
    local key
    for key in WP_ADMIN_PASSWORD WP_DB_PASSWORD WP_DB_ROOT_PASSWORD; do
        if ! grep -Eq "^${key}=[[:xdigit:]]{64}$" "$ENV_FILE"; then
            if grep -q "^${key}=" "$ENV_FILE"; then
                die "$key exists but is not a valid 64-character hex secret; configure it securely."
            fi
            printf '%s=%s\n' "$key" "$(make_secret)" >> "$ENV_FILE"
        fi
    done
}

get_env_value() {
    local key="$1" line
    line="$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1 || true)"
    line="${line#*=}"
    line="${line%\"}"
    line="${line#\"}"
    printf '%s' "$line"
}

validate_env() {
    local bind_ip site_url port
    bind_ip="$(get_env_value WP_BIND_IP)"
    port="$(get_env_value WP_PORT)"
    site_url="$(get_env_value WP_SITE_URL)"
    [[ "$bind_ip" == 127.0.0.1 ]] || die 'Installer binds to loopback only; configure external HTTPS routing separately.'
    [[ "$port" =~ ^[0-9]{2,5}$ ]] && ((10#$port >= 1024 && 10#$port <= 65535)) || die 'WP_PORT must be an unprivileged TCP port (1024-65535).'
    [[ "$site_url" =~ ^https?://[^[:space:]]+$ ]] || die 'WP_SITE_URL must be an HTTP(S) URL.'
    [[ "$site_url" != *'@'* ]] || die 'WP_SITE_URL cannot contain credentials.'
    local key value
    for key in WP_ADMIN_PASSWORD WP_DB_PASSWORD WP_DB_ROOT_PASSWORD; do
        value="$(get_env_value "$key")"
        [[ "$value" =~ ^[[:xdigit:]]{64}$ ]] || die "Invalid $key."
    done
    [[ "$(get_env_value WP_ADMIN_USER)" != admin ]] || die 'Select a non-default WordPress administrator username.'
}

docker_check() {
    command -v docker >/dev/null 2>&1 || die 'Docker is missing. Install Docker Engine + Compose V2.'
    docker compose version >/dev/null 2>&1 || die 'Docker Compose V2 is missing.'
    docker info >/dev/null 2>&1 || die 'Docker daemon is unavailable or your user lacks permission.'
}

compose() { docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"; }

command_name="${1:-install}"
case "$command_name" in
    --help|-h|help) usage; exit 0 ;;
    --dry-run)
        check_sources
        cat <<'STEPS'
Dry run: no .env is written and no Docker commands are executed.
1. Generate wp-installer/.env with independent 256-bit admin/DB/root secrets.
2. Validate local-only listener and check Docker Compose.
3. Pull the official WordPress, WP-CLI, MariaDB and BusyBox images.
4. Initialize persistent WP volume ownership and wait for healthy MariaDB.
5. Download WordPress from WordPress.org with WP-CLI and verify checksums.
6. Provision wp-config.php and WP database if absent; activate local plugin/theme.
7. Start WordPress on the configured loopback port and check container health.
STEPS
        exit 0 ;;
    install)
        check_sources
        ensure_env
        validate_env
        docker_check
        compose config --quiet
        printf '%s\n' 'Pulling official installation images...'
        compose --profile installer pull db volume-init wpcli wordpress
        printf '%s\n' 'Preparing named WordPress storage...'
        compose run --rm volume-init
        printf '%s\n' 'Starting local MariaDB...'
        compose up -d --wait db
        printf '%s\n' 'Downloading/configuring WordPress via WP-CLI...'
        compose run --rm wpcli
        printf '%s\n' 'Starting WordPress...'
        compose up -d --wait wordpress
        printf '%s\n' 'WordPress staging installer completed.'
        printf 'Website: %s\n' "$(get_env_value WP_SITE_URL)"
        printf 'Login:   %s/wp-login.php\n' "$(get_env_value WP_SITE_URL | sed 's:/*$::')"
        printf 'Admin:   %s\n' "$(get_env_value WP_ADMIN_USER)"
        printf '%s\n' 'Credentials are in wp-installer/.env (mode 0600); do not commit or expose them.'
        ;;
    status|stop)
        [[ -f "$ENV_FILE" ]] || die 'No wp-installer/.env found. Run install first.'
        docker_check
        if [[ "$command_name" == status ]]; then compose ps; else compose stop wordpress db; fi
        ;;
    *) usage >&2; die "Unknown command: $command_name" ;;
esac
