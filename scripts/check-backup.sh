#!/usr/bin/env bash
# Backup integrity + freshness check (exit non-zero on failure for cron alerting).
# Suitable for cron with MAILTO to notify on failure.
set -Eeuo pipefail

BACKUP_DIR="${ZMOVIE_BACKUP_DIR:-/opt/backups/wordpress}"
MAX_AGE_HOURS="${BACKUP_MAX_AGE_HOURS:-26}"

fail(){ printf '[check-backup] FAIL: %s\n' "$*" >&2; exit 1; }

latest="$(ls -t "$BACKUP_DIR"/zmovie-cinema-*.sql.gz 2>/dev/null | head -1 || true)"
[ -n "$latest" ] || fail "no backup file found in $BACKUP_DIR"
[ -s "$latest" ] || fail "latest backup is empty: $latest"

# Freshness: file mtime must be within MAX_AGE_HOURS.
if ! find "$latest" -mmin "-$((MAX_AGE_HOURS * 60))" -print -quit | grep -q .; then
  fail "latest backup is older than ${MAX_AGE_HOURS}h: $latest"
fi

# Decompress once into a scratch file. Piping `zcat` straight into
# `grep -q` is racy: grep exits on the first match, zcat dies on SIGPIPE,
# and `set -o pipefail` then reports the pipeline as failed. That produced
# intermittent false "missing table" alarms on healthy backups.
scratch="$(mktemp)"
trap 'rm -f "$scratch"' EXIT
zcat "$latest" > "$scratch" 2>/dev/null || { rm -f "$scratch"; fail "gzip integrity check failed: $latest"; }

# Content: must contain the core WordPress tables.
for table in wp_posts wp_users wp_options; do
  grep -q 'CREATE TABLE `'"$table"'`' "$scratch" \
    || { rm -f "$scratch"; fail "backup missing table $table: $latest"; }
done

rm -f "$scratch"
printf '[check-backup] OK: %s\n' "$latest"
