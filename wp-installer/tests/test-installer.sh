#!/usr/bin/env bash
set -Eeuo pipefail

source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
mkdir -p "$tmp/repo/wp-installer/scripts" "$tmp/repo/wp-plugins/zwp-cinema" "$tmp/repo/themes/zwp-cinema" "$tmp/bin"
cp "$source_dir/wp-installer/install.sh" "$source_dir/wp-installer/.env.example" \
    "$source_dir/wp-installer/compose.yaml" "$tmp/repo/wp-installer/"
cp "$source_dir/wp-installer/scripts/bootstrap.sh" "$tmp/repo/wp-installer/scripts/"
printf '<?php\n' > "$tmp/repo/wp-plugins/zwp-cinema/zwp-cinema.php"
printf '/* WordPress Theme */\n' > "$tmp/repo/themes/zwp-cinema/style.css"
printf '<?php\n' > "$tmp/repo/themes/zwp-cinema/index.php"

cat > "$tmp/bin/docker" <<'FAKE'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$MOCK_DOCKER_LOG"
case "$*" in
    'info') exit 0 ;;
    'compose version') printf 'Docker Compose mock\n'; exit 0 ;;
    *) exit 0 ;;
esac
FAKE
chmod +x "$tmp/bin/docker"
export MOCK_DOCKER_LOG="$tmp/docker.log"
export PATH="$tmp/bin:$PATH"
script="$tmp/repo/wp-installer/install.sh"

bash "$script" --help > "$tmp/help.txt"
test ! -e "$tmp/repo/wp-installer/.env"
bash "$script" --dry-run > "$tmp/dry.txt"
test ! -e "$tmp/repo/wp-installer/.env"
test ! -e "$MOCK_DOCKER_LOG"

automated="$(bash "$script" 2>&1)"
test -f "$tmp/repo/wp-installer/.env"
test "$(stat -c '%a' "$tmp/repo/wp-installer/.env")" = 600
for key in WP_ADMIN_PASSWORD WP_DB_PASSWORD WP_DB_ROOT_PASSWORD; do
    value="$(sed -n "s/^${key}=//p" "$tmp/repo/wp-installer/.env")"
    [[ "$value" =~ ^[a-f0-9]{64}$ ]] || { echo "Invalid generated secret: $key" >&2; exit 1; }
    [[ "$automated" != *"$value"* ]] || { echo 'Installer disclosed a generated secret' >&2; exit 1; }
done
secret_count="$(grep -c '^WP_.*PASSWORD=' "$tmp/repo/wp-installer/.env")"
test "$secret_count" -eq 3

test "$(sed -n 's/^WP_ADMIN_PASSWORD=//p' "$tmp/repo/wp-installer/.env")" != "$(sed -n 's/^WP_DB_PASSWORD=//p' "$tmp/repo/wp-installer/.env")"

cp "$tmp/repo/wp-installer/.env" "$tmp/env-before"
bash "$script" > "$tmp/repeat.txt"
cmp -s "$tmp/env-before" "$tmp/repo/wp-installer/.env"

grep -q 'volume-init' "$MOCK_DOCKER_LOG"
grep -q 'up -d --wait db' "$MOCK_DOCKER_LOG"
grep -q 'run --rm wpcli' "$MOCK_DOCKER_LOG"
grep -q 'up -d --wait wordpress' "$MOCK_DOCKER_LOG"
! grep -qE 'down.*(-v|--volumes)|rm .*wp_database' "$MOCK_DOCKER_LOG"

bash "$script" stop > "$tmp/stopped.txt"
grep -q 'stop wordpress db' "$MOCK_DOCKER_LOG"
sed -i 's/^WP_BIND_IP=127.0.0.1$/WP_BIND_IP=0.0.0.0/' "$tmp/repo/wp-installer/.env"
if bash "$script" > "$tmp/unsafe.txt" 2>&1; then
    echo 'A public-facing listener was incorrectly allowed' >&2
    exit 1
fi
grep -q 'loopback only' "$tmp/unsafe.txt"

grep -q 'wp core download' "$source_dir/wp-installer/scripts/bootstrap.sh"
grep -q 'wp core verify-checksums' "$source_dir/wp-installer/scripts/bootstrap.sh"
grep -q 'wp core is-installed' "$source_dir/wp-installer/scripts/bootstrap.sh"
grep -q -- '--prompt=admin_password' "$source_dir/wp-installer/scripts/bootstrap.sh"

printf '%s\n' 'PASS: installer help/dry-run, private random secrets, idempotency, orchestration, non-destructive stop, public-listener rejection.'
