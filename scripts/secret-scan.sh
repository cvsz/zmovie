#!/usr/bin/env bash
# Secret scan over git-tracked files (CI and local use).
#
# Prints file names only, never secret values.
# Exit 0 when clean, exit 1 with ::error annotations on any finding.
#
# Private-key detection is PEM-structure aware: a file is flagged only when
# it contains an opening marker AND a base64-looking body line AND a closing
# marker. Documentation prose that merely names the marker type (no dashes,
# no body, no closing marker) passes. Detected families: generic PKCS8,
# RSA, EC and OpenSSH private keys.
#
# NOTE: this script spells out its own match fragments, so it excludes
# itself from the scan (same approach the workflow used before).
set -Eeuo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

SELF="scripts/secret-scan.sh"
fail=0

# 1) PEM private-key blocks (structure-aware, not phrase-aware).
begin_pat='-----BEGIN ([A-Z0-9 ]+ )?PRIVATE KEY-----'
end_pat='-----END ([A-Z0-9 ]+ )?PRIVATE KEY-----'
body_pat='^[A-Za-z0-9+/=]{32,}$'
candidates="$(git grep --cached -l -E -e "$begin_pat" -- . ":!$SELF" || true)"
if [ -n "$candidates" ]; then
  while IFS= read -r file; do
    [ -n "$file" ] || continue
    content="$(git show ":$file")"
    if printf '%s\n' "$content" | grep -qE -e "$begin_pat" \
      && printf '%s\n' "$content" | grep -qE -e "$end_pat" \
      && printf '%s\n' "$content" | grep -qE -e "$body_pat"; then
      printf '::error::PEM private-key block in tracked file: %s\n' "$file"
      fail=1
    fi
  done <<< "$candidates"
fi

# 2) Previously exposed credential pattern must not return.
if git grep -n --cached -F 'zeaz-cinema-2026' -- . ":!$SELF"; then
  printf '::error::Previously exposed credential pattern found.\n'
  fail=1
fi

# 3) Passwords on CLI flags in scripts (this rule script excluded: it only
# names the pattern, same rationale as steps 1-2).
if git grep -n --cached -E -- '--password=' -- 'scripts/*.sh' 'wp-installer/*.sh' 'install*.sh' ":!$SELF"; then
  printf '::error::Inline --password= flag found in scripts (use --defaults-file or env).\n'
  fail=1
fi

# 4) Env files must never be tracked (.example templates are allowed).
if git ls-files | grep -E '(^|/)\.env$|(^|/)\.env\.' | grep -v '\.example$'; then
  printf '::error::Env file tracked in git.\n'
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "Secret scan passed."
fi
exit "$fail"
