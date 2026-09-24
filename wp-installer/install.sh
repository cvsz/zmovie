#!/usr/bin/env bash
set -Eeuo pipefail

log() { printf '[wp-installer] %s\n' "$*"; }
die() { printf '[wp-installer] ERROR: %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"; }

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${WP_INSTALLER_ENV:-$SCRIPT_DIR/.env}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

: "${WP_PATH:=/var/www/zmovie-cinema}"
: "${WP_VERSION:=latest}"
: "${WP_LOCALE:=en_US}"
: "${DB_HOST:=127.0.0.1}"
: "${DB_PORT:=3306}"
: "${DB_PREFIX:=wp_}"
: "${DB_AUTO_CREATE:=false}"
: "${DB_ROOT_USER:=root}"
: "${INSTALL_PLUGIN:=true}"
: "${INSTALL_THEME:=true}"
: "${ACTIVATE_THEME:=true}"
: "${CREATE_CINEMA_PAGES:=true}"
: "${VERIFY_CHECKSUMS:=true}"
: "${FORCE_CORE_DOWNLOAD:=false}"

for name in WP_URL WP_TITLE WP_ADMIN_USER WP_ADMIN_EMAIL WP_ADMIN_PASSWORD DB_NAME DB_USER DB_PASSWORD; do
  [[ -n "${!name:-}" ]] || die "missing required environment variable: $name"
done

[[ "$WP_URL" =~ ^https?://[^[:space:]]+$ ]] || die "WP_URL must be a valid http(s) URL"
[[ "$DB_PREFIX" =~ ^[A-Za-z0-9_]+$ ]] || die "DB_PREFIX may contain only letters, digits, and underscore"
[[ "$WP_ADMIN_EMAIL" == *@*.* ]] || die "WP_ADMIN_EMAIL does not look valid"

need php
need curl
need tar
need rsync
need mktemp

WP_CLI_BIN="${WP_CLI_BIN:-}"
WP_CLI_MODE=exec
if [[ -z "$WP_CLI_BIN" ]]; then
  if command -v wp >/dev/null 2>&1; then
    WP_CLI_BIN="$(command -v wp)"
  else
    WP_CLI_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/zmovie-wp-installer"
    WP_CLI_BIN="$WP_CLI_DIR/wp-cli.phar"
    WP_CLI_MODE=phar
    mkdir -p "$WP_CLI_DIR"
    if [[ ! -s "$WP_CLI_BIN" ]]; then
      log "downloading WP-CLI official Phar"
      tmp_wpcli="$(mktemp "$WP_CLI_DIR/wp-cli.phar.XXXXXX")"
      trap 'rm -f "${tmp_wpcli:-}"' EXIT
      curl --fail --location --proto '=https' --tlsv1.2 https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar --output "$tmp_wpcli"
      php "$tmp_wpcli" --info >/dev/null || die "downloaded WP-CLI Phar failed validation"
      chmod 0755 "$tmp_wpcli"
      mv "$tmp_wpcli" "$WP_CLI_BIN"
      tmp_wpcli=
      trap - EXIT
    fi
  fi
elif [[ "$WP_CLI_BIN" == *.phar ]]; then
  WP_CLI_MODE=phar
fi

wp_raw() {
  if [[ "$WP_CLI_MODE" == "phar" ]]; then
    php "$WP_CLI_BIN" "$@"
  else
    "$WP_CLI_BIN" "$@"
  fi
}

wp() {
  wp_raw --path="$WP_PATH" --allow-root "$@"
}

wp_raw --info >/dev/null || die "WP-CLI bootstrap failed"

if [[ "$DB_AUTO_CREATE" == "true" ]]; then
  need mysql
  [[ -n "${DB_ROOT_PASSWORD:-}" ]] || die "DB_AUTO_CREATE=true requires DB_ROOT_PASSWORD"
  [[ "$DB_NAME" =~ ^[A-Za-z0-9_]+$ ]] || die "DB_NAME contains unsupported characters for auto-create"
  [[ "$DB_USER" =~ ^[A-Za-z0-9_]+$ ]] || die "DB_USER contains unsupported characters for auto-create"

  log "creating database/user when absent"
  MYSQL_PWD="$DB_ROOT_PASSWORD" mysql     --host="$DB_HOST" --port="$DB_PORT" --user="$DB_ROOT_USER"     --protocol=TCP --batch --skip-column-names <<SQL
CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';
ALTER USER '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'%';
FLUSH PRIVILEGES;
SQL
fi

mkdir -p "$WP_PATH"

if [[ ! -f "$WP_PATH/wp-includes/version.php" ]]; then
  log "downloading WordPress $WP_VERSION ($WP_LOCALE)"
  download_args=(core download "--version=$WP_VERSION" "--locale=$WP_LOCALE" --skip-content)
  [[ "$FORCE_CORE_DOWNLOAD" == "true" ]] && download_args+=(--force)
  wp "${download_args[@]}"
else
  log "WordPress core already present; skipping core download"
fi

if [[ "$VERIFY_CHECKSUMS" == "true" ]]; then
  log "verifying WordPress core checksums"
  wp core verify-checksums --include-root
fi

if [[ ! -f "$WP_PATH/wp-config.php" ]]; then
  log "creating wp-config.php"
  printf '%s\n' "$DB_PASSWORD" | wp config create     "--dbname=$DB_NAME"     "--dbuser=$DB_USER"     "--dbhost=$DB_HOST:$DB_PORT"     "--dbprefix=$DB_PREFIX"     --dbcharset=utf8mb4     --prompt=dbpass     --skip-check

  # Read first-party license values from process environment at runtime.
  wp config set ZEAZ_LICENSE_API "getenv('ZEAZ_LICENSE_API') ?: ''" --raw
  wp config set ZEAZ_LICENSE_ORIGIN "getenv('ZEAZ_LICENSE_ORIGIN') ?: ''" --raw
  wp config set ZEAZ_LICENSE_KEY "getenv('ZEAZ_LICENSE_KEY') ?: ''" --raw
  wp config set ZEAZ_LICENSE_PUBLIC_KEY "getenv('ZEAZ_LICENSE_PUBLIC_KEY') ?: ''" --raw
  wp config set DISALLOW_FILE_EDIT true --raw
  wp config set FORCE_SSL_ADMIN true --raw
else
  log "wp-config.php already exists; preserving existing configuration"
fi

if ! wp core is-installed >/dev/null 2>&1; then
  log "installing WordPress database"
  printf '%s\n' "$WP_ADMIN_PASSWORD" | wp core install     "--url=$WP_URL"     "--title=$WP_TITLE"     "--admin_user=$WP_ADMIN_USER"     "--admin_email=$WP_ADMIN_EMAIL"     "--locale=$WP_LOCALE"     --skip-email     --prompt=admin_password
else
  log "WordPress database already installed; skipping core install"
fi

install_local_component() {
  local kind="$1" src="$2" dest="$3"
  [[ -d "$src" ]] || die "missing repository source: $src"
  mkdir -p "$dest"
  rsync -a --delete --exclude='.git' "$src/" "$dest/"
  log "installed local $kind source into $dest"
}

if [[ "$INSTALL_PLUGIN" == "true" ]]; then
  install_local_component plugin     "$REPO_ROOT/wp-plugins/zwp-cinema"     "$WP_PATH/wp-content/plugins/zwp-cinema"
  wp plugin activate zwp-cinema
fi

if [[ "$INSTALL_THEME" == "true" ]]; then
  install_local_component theme     "$REPO_ROOT/themes/zwp-cinema"     "$WP_PATH/wp-content/themes/zwp-cinema"
  if [[ "$ACTIVATE_THEME" == "true" ]]; then
    wp theme activate zwp-cinema
  fi
fi

if [[ "$CREATE_CINEMA_PAGES" == "true" ]]; then
  if ! wp post list --post_type=page --name=favorites --field=ID --format=ids | grep -q '[0-9]'; then
    wp post create --post_type=page --post_status=publish       --post_title='Favorites' --post_name='favorites'       --post_content='[zwpc_favorites]' >/dev/null
    log "created Favorites page"
  fi
  if ! wp post list --post_type=page --name=submit-film --field=ID --format=ids | grep -q '[0-9]'; then
    wp post create --post_type=page --post_status=publish       --post_title='Submit Film' --post_name='submit-film'       --post_content='[zwpc_submit]' >/dev/null
    log "created Submit Film page"
  fi
fi

wp rewrite structure '/%postname%/' --hard
wp rewrite flush --hard
wp cache flush >/dev/null 2>&1 || true

log "running final verification"
wp core is-installed
wp core version
wp plugin status zwp-cinema || true
wp theme status zwp-cinema || true

cat <<EOF

WordPress installation completed.

Site:      $WP_URL
Path:      $WP_PATH
Admin URL: ${WP_URL%/}/wp-admin/

Security reminders:
- Keep WP_ADMIN_PASSWORD, DB_PASSWORD and ZEAZ_LICENSE_KEY in a secret manager.
- Put the site behind HTTPS before exposing wp-admin publicly.
- Run the staging acceptance checklist in wp-plugins/zwp-cinema/README.md.
EOF
