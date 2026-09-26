#!/usr/bin/env bash
# Encrypted off-host backup staging for zMovie.
#
# Scope: build and verify an encrypted, integrity-checked archive of the
# protected DR snapshot plus the latest verified local backups. Replication
# only happens to an operator-approved destination that already exists on
# this host. There is deliberately no default remote: uploading production
# backups anywhere without an approved credential and destination is a
# policy violation, so the script refuses to guess one.
#
# Encryption: AES-256-CBC with PBKDF2-HMAC-SHA256 (OpenSSL 3 default KDF).
# The passphrase is read from a root-only file and is never passed on the
# command line, so it cannot leak through `ps` or shell history.
#
# Passphrase file (create once, root only, 0600):
#   sudo install -d -m 700 /etc/zmovie
#   sudo sh -c 'umask 077; openssl rand -base64 48 > /etc/zmovie/offsite.key'
# Optional destination (root only, 0600), KEY=VALUE lines:
#   ZMOVIE_OFFSITE_DEST=/mnt/zmovie-storage/backups
#   ZMOVIE_OFFSITE_RETENTION=14
#
# Usage:
#   sudo bash scripts/backup-offsite.sh            # build + verify + stage
#   ZMOVIE_OFFSITE_DRYRUN=1 sudo bash scripts/backup-offsite.sh
set -Eeuo pipefail

KEY_FILE="${ZMOVIE_OFFSITE_KEY_FILE:-/etc/zmovie/offsite.key}"
STAGE_DIR="${ZMOVIE_OFFSITE_STAGE_DIR:-/var/backups/zmovie/offsite}"
DR_ROOT="/opt/backups/dr"
WP_BACKUP_DIR="${ZMOVIE_BACKUP_DIR:-/opt/backups/wordpress}"
SQLITE_BACKUP_DIR="${ZMOVIE_SQLITE_BACKUP_DIR:-/var/backups/zmovie}"
RETENTION="${ZMOVIE_OFFSITE_RETENTION:-14}"
DRYRUN="${ZMOVIE_OFFSITE_DRYRUN:-0}"

log(){ printf '[backup-offsite] %s\n' "$*"; }
fail(){ printf '[backup-offsite] FAIL: %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || fail "must run as root (needs key file and backup reads)"

# 1) Preconditions -------------------------------------------------------------
[[ -r "$KEY_FILE" ]] || fail "passphrase file $KEY_FILE is missing or unreadable"
key_mode="$(stat -c '%a' "$KEY_FILE")"
[[ "$key_mode" == "600" ]] || fail "passphrase file $KEY_FILE must be mode 600 (found $key_mode)"
[[ -d "$DR_ROOT" ]] || fail "no DR snapshots at $DR_ROOT; run scripts/backup-dr.sh first"

latest_dr="$(find "$DR_ROOT" -mindepth 1 -maxdepth 1 -type d | sort | tail -1)"
[[ -n "$latest_dr" ]] || fail "no DR snapshot directory found under $DR_ROOT"

latest_wp="$(ls -t "$WP_BACKUP_DIR"/zmovie-cinema-*.sql.gz 2>/dev/null | head -1 || true)"
latest_sqlite="$(ls -t "$SQLITE_BACKUP_DIR"/*.db 2>/dev/null | head -1 || true)"

# 2) Build the encrypted archive ----------------------------------------------
install -d -m 700 "$STAGE_DIR"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

mkdir -p "$work/payload"
cp -a "$latest_dr" "$work/payload/dr-snapshot"
[[ -n "$latest_wp" ]] && cp -a "$latest_wp" "$work/payload/" || log "WARN: no WordPress backup found"
[[ -n "$latest_sqlite" ]] && cp -a "$latest_sqlite" "$work/payload/" || log "WARN: no SQLite backup found"

# Exclude the manifest itself: hashing it would be self-referential and racy.
( cd "$work/payload" && find . -type f ! -name MANIFEST.sha256 -exec sha256sum {} + | sort -k2 > MANIFEST.sha256 )

archive="$STAGE_DIR/zmovie-dr-$TS.tar.gz"
tar -czf "$work/payload.tar" -C "$work" payload
# -pass file:... keeps the passphrase out of argv and out of `ps` output.
openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -salt \
  -in "$work/payload.tar" -out "$archive" -pass "file:$KEY_FILE"
chmod 600 "$archive"
sha256sum "$archive" > "$archive.sha256"
log "encrypted archive: $archive ($(stat -c %s "$archive") bytes)"

# 3) Verify the archive decrypts and matches its own manifest ------------------
verify_dir="$(mktemp -d)"
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 \
  -in "$archive" -out "$verify_dir/payload.tar" -pass "file:$KEY_FILE"
tar -xzf "$verify_dir/payload.tar" -C "$verify_dir"
( cd "$verify_dir/payload" && sha256sum -c MANIFEST.sha256 >/dev/null )
rm -rf "$verify_dir"
log "decrypt + manifest verification OK"

# 4) Retention (local staged copies only) -------------------------------------
mapfile -t old < <(ls -t "$STAGE_DIR"/zmovie-dr-*.tar.gz 2>/dev/null | tail -n +$((RETENTION + 1)))
for f in "${old[@]:-}"; do
  [[ -n "$f" ]] || continue
  rm -f "$f" "$f.sha256"
  log "pruned old staged archive: $(basename "$f")"
done

# 5) Replicate only to an already-approved, already-present destination ------
dest=""
if [[ -r /etc/zmovie/offsite.env ]]; then
  # shellcheck disable=SC1091
  source /etc/zmovie/offsite.env
  dest="${ZMOVIE_OFFSITE_DEST:-}"
fi

if [[ -z "$dest" ]]; then
  log "BLOCKED: no approved off-host destination configured."
  log "Encrypted archive is staged and verified at $STAGE_DIR."
  log "Set ZMOVIE_OFFSITE_DEST in /etc/zmovie/offsite.env (root 0600) to enable replication."
  exit 0
fi
if [[ ! -d "$dest" ]]; then
  log "BLOCKED: configured destination $dest does not exist on this host."
  log "Encrypted archive remains staged and verified at $STAGE_DIR."
  exit 0
fi

if [[ "$DRYRUN" == "1" ]]; then
  log "DRYRUN: would copy $(basename "$archive") to $dest"
  exit 0
fi

install -d -m 700 "$dest"
install -m 600 "$archive" "$archive.sha256" "$dest/"
log "replicated $(basename "$archive") to $dest"
