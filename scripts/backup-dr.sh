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

# 1) License key material (active + pinned public)
mkdir -p "$OUT/zeaz-keys"
cp -p /home/cvsz/.config/zeaz/license_server_private_key.pem "$OUT/zeaz-keys/" 2>/dev/null || log "WARN: server private key not found"
cp -p /home/cvsz/.config/zeaz/license_server_public_key.pem "$OUT/zeaz-keys/" 2>/dev/null || log "WARN: server public key not found"
chmod 600 "$OUT"/zeaz-keys/* 2>/dev/null || true

# 2) Service configuration (no databases)
mkdir -p "$OUT/config"
for f in /etc/zmovie/zmovie.env /etc/zmovie/zmovie-staging.env \
         /etc/zmovie-cinema/license.env /etc/zmovie-cinema/license-admin.env \
         /etc/zmovie-cinema/license-server.env \
         /etc/php/8.5/fpm/pool.d/zmovie-cinema-env.conf \
         /etc/nginx/sites-available/zmovie-cinema /etc/nginx/sites-available/license-zeaz \
         /etc/systemd/system/zeaz-license.service /etc/systemd/system/zmovie-staging.service \
         /etc/cloudflared-zaffiliate/config.yml; do
  [[ -f "$f" ]] && cp -p "$f" "$OUT/config/" || log "WARN: missing $f"
done
chmod 600 "$OUT"/config/*

# 3) Small media set (SQLite DBs are covered by their own verified backups)
mkdir -p "$OUT/media"
tar -czf "$OUT/media/var-lib-zmovie-media.tar.gz" -C /var/lib/zmovie media exports 2>/dev/null \
  || log "WARN: media archive partial"

# 4) Integrity manifest (names + hashes only; excludes itself)
(cd "$OUT" && find . -type f ! -name SHA256SUMS -exec sha256sum {} + | sort -k2 > SHA256SUMS)
chmod 600 "$OUT/SHA256SUMS"
log "snapshot complete: $OUT"
log "verify anytime with: (cd $OUT && sha256sum -c SHA256SUMS)"
