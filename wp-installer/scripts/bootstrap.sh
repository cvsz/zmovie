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

# The explicit WordPress.org ZIP avoids WP-CLI PharData truncating TAR paths >100 bytes.
if [ "${WP_VERSION:-latest}" = latest ]; then
    WP_ZIP_URL="https://wordpress.org/latest.zip"
else
    WP_ZIP_URL="https://wordpress.org/wordpress-${WP_VERSION}.zip"
fi

download_wordpress_core() {
    wp core download "$WP_ZIP_URL" --path="$WP_PATH" --force
}

if [ ! -f "$WP_PATH/wp-settings.php" ]; then
    printf '%s\n' 'Downloading official WordPress ZIP via WP-CLI...'
    download_wordpress_core
elif [ ! -f "$WP_PATH/wp-config.php" ] &&
     ! wp core verify-checksums --path="$WP_PATH" --locale=en_US >/dev/null 2>&1; then
    printf '%s\n' 'Recovering a partial first-install WordPress core from official ZIP...'
    # Only an unconfigured WordPress may have its broken core AI library replaced.
    # Leave wp-content, persistent volumes, and all configured installations intact.
    if [ -d "$WP_PATH/wp-includes/php-ai-client" ]; then
        rm -rf -- "$WP_PATH/wp-includes/php-ai-client"
    fi
    download_wordpress_core
else
    printf '%s\n' 'WordPress core already present; preserving installed files.'
fi

printf '%s\n' 'Verifying WordPress.org core checksums (en_US ZIP)...'
wp core verify-checksums --path="$WP_PATH" --locale=en_US

if [ ! -f "$WP_PATH/wp-config.php" ]; then
    printf '%s\n' 'Creating wp-config.php (database password passed through standard input)...'
    if ! printf '%s\n' "$WP_DB_PASSWORD" | wp config create \
        --path="$WP_PATH" --dbname="$WP_DB_NAME" --dbuser="$WP_DB_USER" \
        --dbhost=db:3306 --dbprefix="$WP_DB_PREFIX" --prompt=dbpass --skip-check >/dev/null 2>&1; then
        printf '%s\n' 'Creating wp-config.php failed; sensitive WP-CLI prompt output was withheld.' >&2
        exit 1
    fi
    printf '%s\n' 'wp-config.php created successfully.'
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
    if ! printf '%s\n' "$WP_ADMIN_PASSWORD" | wp core install \
        --path="$WP_PATH" --url="$WP_SITE_URL" --title="$WP_SITE_TITLE" \
        --admin_user="$WP_ADMIN_USER" --admin_email="$WP_ADMIN_EMAIL" \
        --prompt=admin_password --skip-email >/dev/null 2>&1; then
        printf '%s\n' 'Installing WordPress failed; sensitive WP-CLI prompt output was withheld.' >&2
        exit 1
    fi
    printf '%s\n' 'WordPress database initialized successfully.'
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
    wp rewrite structure '/%postname%/' --hard --path="$WP_PATH"
    wp rewrite flush --hard --path="$WP_PATH"
    if [ ! -s "$WP_PATH/.htaccess" ]; then
        printf '%s\n' 'Apache rewrite rules were not generated; refusing incomplete installation.' >&2
        exit 1
    fi
    if [ "${WP_LOCALE:-en_US}" != en_US ]; then
        wp language core install "$WP_LOCALE" --activate --path="$WP_PATH"
    fi
else
    printf '%s\n' 'Existing active theme and permalink configuration preserved.'
fi

printf 'WordPress: %s\n' "$(wp core version --path="$WP_PATH")"
printf '%s\n' 'ZeaZ Cinema plugin and theme provisioning completed.'
