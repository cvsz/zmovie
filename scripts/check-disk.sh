#!/usr/bin/env bash
# Disk utilization check (exit non-zero on breach for cron alerting).
# Thresholds can be overridden: DISK_WARN_PCT (default 85), DISK_CRIT_PCT (default 95).
set -Eeuo pipefail

WARN="${DISK_WARN_PCT:-85}"
CRIT="${DISK_CRIT_PCT:-95}"
PATHS=("$@" )
(( ${#PATHS[@]} )) || PATHS=(/ /var/lib/zmovie /opt/backups)

fail(){ printf '[check-disk] FAIL: %s\n' "$*" >&2; exit 1; }
[[ "$WARN" =~ ^[0-9]+$ && "$CRIT" =~ ^[0-9]+$ ]] || fail "thresholds must be integers"

worst=0
for target in "${PATHS[@]}"; do
  use="$(df --output=pcent "$target" 2>/dev/null | tail -1 | tr -dc '0-9')"
  [[ -n "$use" ]] || fail "cannot read disk usage for $target"
  printf '[check-disk] %s use=%s%%\n' "$target" "$use"
  (( use > worst )) && worst="$use"
done
(( worst >= CRIT )) && fail "critical disk usage ${worst}% (>= ${CRIT}%)"
(( worst >= WARN )) && fail "warning disk usage ${worst}% (>= ${WARN}%)"
echo "[check-disk] OK worst=${worst}%"
