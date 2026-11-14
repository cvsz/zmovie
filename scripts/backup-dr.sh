#!/usr/bin/env bash
# Protected DR snapshot: license keys + service configs + small media set.
# Root-only. No secrets are printed. Run weekly via cron; see runbook.
# Output: /opt/backups/dr/<TIMESTAMP>/ with SHA256SUMS.
set -Eeuo pipefail

OUT_ROOT="/opt/backups/dr"
TS="$(date +%Y%m%d-%H%M%S)"
OUT="$OUT_ROOT/$TS"
mkdir -p "$OUT"
chmod 700 "$OUT_ROOT" "$OUT"

log(){ printf '[backup-dr] %s\n' "$*"; }
[[ "$(id -u)" -eq 0 ]] || { log "must run as root"; exit 1; }

# 1) License key material and durable license state
mkdir -p "$OUT/zeaz-keys"
cp -p /home/cvsz/.config/zeaz/license_server_private_key.pem "$OUT/zeaz-keys/" 2>/dev/null || log "WARN: server private key not found"
cp -p /home/cvsz/.config/zeaz/license_server_public_key.pem "$OUT/zeaz-keys/" 2>/dev/null || log "WARN: server public key not found"
if [[ -f /home/cvsz/.config/zeaz/licenses.sqlite3 ]]; then
  python3 - /home/cvsz/.config/zeaz/licenses.sqlite3 "$OUT/zeaz-keys/licenses.sqlite3" <<'PY'
import sqlite3
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
    src.backup(dst)
    result = dst.execute("PRAGMA quick_check").fetchone()
    if result is None or str(result[0]).lower() != "ok":
        raise SystemExit(f"License database integrity check failed: {result}")
PY
  chmod 600 "$OUT/zeaz-keys/licenses.sqlite3"
else
  log "WARN: license database not found"
fi
chmod 600 "$OUT"/zeaz-keys/* 2>/dev/null || true

# 2) Service configuration (no databases)
mkdir -p "$OUT/config"
for f in /etc/zmovie/zmovie.env /etc/zmovie/zmovie-staging.env \
         /etc/zmovie-cinema/license.env /etc/zmovie-cinema/license-admin.env \
         /etc/zmovie-cinema/license-server.env \
         /etc/php/8.5/fpm/pool.d/zmovie-cinema-env.conf \
         /etc/nginx/sites-available/zmovie-cinema /etc/nginx/sites-available/license-zeaz \
/etc/systemd/system/zeaz-license.service /etc/systemd/system/zmovie-staging.service; do
# shellcheck disable=SC2015
  [[ -f "$f" ]] && cp -p "$f" "$OUT/config/" || log "WARN: missing $f"
done
chmod 600 "$OUT"/config/*

# 3) Small media set (SQLite DBs are covered by their own verified backups)
mkdir -p "$OUT/media"
tar -czf "$OUT/media/var-lib-zmovie-media.tar.gz" -C /var/lib/zmovie media exports 2>/dev/null \
  || log "WARN: media archive partial"

# 4) Integrity manifest (names + hashes only; excludes itself)
# shellcheck disable=SC2094
(cd "$OUT" && find . -type f ! -name SHA256SUMS -exec sha256sum {} + | sort -k2 > SHA256SUMS)
chmod 600 "$OUT/SHA256SUMS"
log "snapshot complete: $OUT"
log "verify anytime with: (cd $OUT && sha256sum -c SHA256SUMS)"
