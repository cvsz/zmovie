#!/bin/sh
set -eu

WP_PATH="${WP_PATH:-/var/www/html}"
WP_CLI_CACHE_DIR="${WP_CLI_CACHE_DIR:-/tmp/zeaz-wp-cli-cache}"
export WP_CLI_CACHE_DIR
if ! mkdir -p "$WP_CLI_CACHE_DIR" || [ ! -w "$WP_CLI_CACHE_DIR" ]; then
    printf 'WP-CLI cache directory is not writable: %s\n' "$WP_CLI_CACHE_DIR" >&2
    exit 2
fi
cd "$WP_PATH"

required="WP_SITE_URL WP_SITE_TITLE WP_ADMIN_USER WP_ADMIN_EMAIL WP_ADMIN_PASSWORD WP_DB_NAME WP_DB_USER WP_DB_PASSWORD WP_DB_PREFIX"
for name in $required; do
    eval "value=\${$name-}"
    if [ -z "$value" ]; then
        printf 'Missing required setting: %s\n' "$name" >&2
        exit 2
    fi
done

if ! printf '%s' "${WP_VERSION:-latest}" | grep -Eq '^(latest|[0-9]+(\.[0-9]+){1,3})$'; then
    printf 'Invalid WordPress version\n' >&2
    exit 2
fi
if ! printf '%s' "${WP_LOCALE:-en_US}" | grep -Eq '^[a-z]{2}(_[A-Z]{2})?$'; then
    printf 'Invalid WordPress locale\n' >&2
    exit 2
fi
if ! printf '%s' "$WP_DB_PREFIX" | grep -Eq '^[a-zA-Z_][a-zA-Z0-9_]*$'; then
    printf 'Invalid WordPress table prefix\n' >&2
    exit 2
fi

if [ ! -f "$WP_PATH/wp-settings.php" ]; then
    printf '%s\n' 'Downloading official WordPress core using WP-CLI...'
    wp core download --path="$WP_PATH" --version="${WP_VERSION:-latest}" --locale="${WP_LOCALE:-en_US}" --force
elif [ ! -f "$WP_PATH/wp-config.php" ] &&
     ! wp core verify-checksums --path="$WP_PATH" --locale="${WP_LOCALE:-en_US}" >/dev/null 2>&1; then
    printf '%s\n' 'An unfinished first-install download was detected; safely re-downloading WordPress core...'
    wp core download --path="$WP_PATH" --version="${WP_VERSION:-latest}" --locale="${WP_LOCALE:-en_US}" --force
else
    printf '%s\n' 'WordPress core already present; preserving installed files.'
fi

printf '%s\n' 'Verifying WordPress.org core checksums...'
wp core verify-checksums --path="$WP_PATH" --locale="${WP_LOCALE:-en_US}"

if [ ! -f "$WP_PATH/wp-config.php" ]; then
    printf '%s\n' 'Creating wp-config.php (database password passed through standard input)...'
    printf '%s\n' "$WP_DB_PASSWORD" | wp config create \
        --path="$WP_PATH" --dbname="$WP_DB_NAME" --dbuser="$WP_DB_USER" \
        --dbhost=db:3306 --dbprefix="$WP_DB_PREFIX" --prompt=dbpass --skip-check
    wp config set DISALLOW_FILE_EDIT true --raw --path="$WP_PATH"
    if [ "${WP_SITE_URL#https://}" != "$WP_SITE_URL" ]; then
        wp config set FORCE_SSL_ADMIN true --raw --path="$WP_PATH"
    fi
else
    printf '%s\n' 'Existing wp-config.php preserved.'
fi

fresh_install=0
if ! wp core is-installed --path="$WP_PATH" >/dev/null 2>&1; then
    printf '%s\n' 'Installing WordPress database and first administrator...'
    printf '%s\n' "$WP_ADMIN_PASSWORD" | wp core install \
        --path="$WP_PATH" --url="$WP_SITE_URL" --title="$WP_SITE_TITLE" \
        --admin_user="$WP_ADMIN_USER" --admin_email="$WP_ADMIN_EMAIL" \
        --prompt=admin_password --skip-email
    fresh_install=1
else
    existing_url="$(wp option get home --path="$WP_PATH")"
    if [ "$existing_url" != "$WP_SITE_URL" ]; then
        printf 'Existing site URL differs (%s); refusing silent URL replacement.\n' "$existing_url" >&2
        exit 3
    fi
    printf '%s\n' 'Existing WordPress database preserved; no administrator reset.'
fi

if ! wp plugin is-active zwp-cinema --path="$WP_PATH" >/dev/null 2>&1; then
    wp plugin activate zwp-cinema --path="$WP_PATH"
else
    printf '%s\n' 'ZeaZ Cinema plugin is already active.'
fi

if [ "$fresh_install" -eq 1 ]; then
    wp theme activate zwp-cinema --path="$WP_PATH"
    wp rewrite structure '/%postname%/' --path="$WP_PATH"
    wp rewrite flush --path="$WP_PATH"
else
    printf '%s\n' 'Existing active theme and permalink configuration preserved.'
fi

printf 'WordPress: %s\n' "$(wp core version --path="$WP_PATH")"
printf '%s\n' 'ZeaZ Cinema plugin and theme provisioning completed.'
