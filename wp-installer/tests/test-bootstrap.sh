#!/usr/bin/env bash
set -Eeuo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
mkdir -p "$tmp/bin" "$tmp/html"
cat > "$tmp/bin/wp" <<'MOCK'
#!/usr/bin/env bash
set -Eeuo pipefail
printf '%s\n' "$*" >> "$WP_TEST_LOG"
case "$1 $2" in
    'core download') touch "$WP_PATH/wp-settings.php" "$WP_PATH/.core-complete" ;;
    'core verify-checksums') test -f "$WP_PATH/.core-complete" ;;
    'core is-installed') test -f "$WP_PATH/.wp-installed" ;;
    'core install')
        IFS= read -r password
        test "$password" = "$WP_ADMIN_PASSWORD"
        touch "$WP_PATH/.wp-installed"
        ;;
    'config create')
        IFS= read -r password
        test "$password" = "$WP_DB_PASSWORD"
        touch "$WP_PATH/wp-config.php"
        ;;
    'plugin is-active') test -f "$WP_PATH/.plugin-active" ;;
    'plugin activate') touch "$WP_PATH/.plugin-active" ;;
    'option get') printf '%s\n' "${WP_EXISTING_URL:-$WP_SITE_URL}" ;;
    'core version') printf '%s\n' '7.1.2' ;;
esac
MOCK
chmod +x "$tmp/bin/wp"
export PATH="$tmp/bin:$PATH"
export WP_TEST_LOG="$tmp/wp.log"
export WP_PATH="$tmp/html"
export WP_SITE_URL=http://127.0.0.1:8090
export WP_SITE_TITLE='ZeaZ Cinema Test'
export WP_ADMIN_USER=cinema_owner
export WP_ADMIN_EMAIL=admin@example.invalid
export WP_ADMIN_PASSWORD='test-only-admin-secret'
export WP_DB_NAME=zeaz_cinema
export WP_DB_USER=zeaz_wp
export WP_DB_PASSWORD='test-only-db-secret'
export WP_DB_PREFIX=zwp_
export WP_LOCALE=en_US
export WP_VERSION=latest
export WP_CLI_CACHE_DIR="$tmp/wp-cli-cache"

bash "$root/wp-installer/scripts/bootstrap.sh" > "$tmp/first.log"
for marker in wp-settings.php wp-config.php .wp-installed .plugin-active; do
    test -f "$tmp/html/$marker" || { echo "Missing bootstrap marker $marker" >&2; exit 1; }
done
grep -q 'core download' "$WP_TEST_LOG"
grep -q 'core download https://wordpress.org/latest.zip' "$WP_TEST_LOG"
grep -q 'core verify-checksums' "$WP_TEST_LOG"
grep -q 'theme activate zwp-cinema' "$WP_TEST_LOG"
! grep -Eq 'test-only-(admin|db)-secret' "$WP_TEST_LOG"
cp "$WP_TEST_LOG" "$tmp/first-commands.log"

bash "$root/wp-installer/scripts/bootstrap.sh" > "$tmp/second.log"
! grep -q 'core download' <(tail -n +"$(($(wc -l < "$tmp/first-commands.log") + 1))" "$WP_TEST_LOG")
! grep -q 'core install' <(tail -n +"$(($(wc -l < "$tmp/first-commands.log") + 1))" "$WP_TEST_LOG")
! grep -q 'theme activate' <(tail -n +"$(($(wc -l < "$tmp/first-commands.log") + 1))" "$WP_TEST_LOG")

# Resume an interrupted first-time extraction without destroying a real installation.
original_wp_path="$WP_PATH"
mkdir -p "$tmp/partial"
touch "$tmp/partial/wp-settings.php"
export WP_PATH="$tmp/partial"
before_resume="$(wc -l < "$WP_TEST_LOG")"
bash "$root/wp-installer/scripts/bootstrap.sh" > "$tmp/recovery.log"
grep -q 'Recovering a partial first-install WordPress core' "$tmp/recovery.log"
test -f "$tmp/partial/.core-complete"
test -f "$tmp/partial/.wp-installed"
tail -n +"$((before_resume + 1))" "$WP_TEST_LOG" | grep -q 'core download'
export WP_PATH="$original_wp_path"

# Never automatically overwrite installed WordPress core with invalid checksums.
rm -f "$WP_PATH/.core-complete"
before_corruption="$(wc -l < "$WP_TEST_LOG")"
if bash "$root/wp-installer/scripts/bootstrap.sh" > "$tmp/corrupt.log" 2>&1; then
    echo 'Bootstrap silently accepted a corrupted installed WordPress core' >&2
    exit 1
fi
if tail -n +"$((before_corruption + 1))" "$WP_TEST_LOG" | grep -q 'core download'; then
    echo 'Bootstrap overwrote an existing installation without approval' >&2
    exit 1
fi
touch "$WP_PATH/.core-complete"

export WP_EXISTING_URL=https://another.example.invalid
if bash "$root/wp-installer/scripts/bootstrap.sh" > "$tmp/mismatch.log" 2>&1; then
    echo 'Bootstrap accepted a changed existing site URL' >&2
    exit 1
fi
grep -q 'refusing silent URL replacement' "$tmp/mismatch.log"
unset WP_EXISTING_URL

export WP_DB_PREFIX='wp_; DROP TABLE users;'
if bash "$root/wp-installer/scripts/bootstrap.sh" > "$tmp/invalid.log" 2>&1; then
    echo 'Bootstrap accepted an invalid table prefix' >&2
    exit 1
fi
grep -q 'Invalid WordPress table prefix' "$tmp/invalid.log"

printf '%s\n' 'PASS: WP-CLI downloads official ZIP, verifies checksums, uses stdin secrets, recovers partial extraction and preserves installed core.'
