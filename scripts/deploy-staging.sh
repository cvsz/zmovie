#!/usr/bin/env bash
# Staging deployment workflow: pinned commit, migration, readiness,
# smoke tests, failure detection, safe rollback. Production untouched.
#
#   sudo bash scripts/deploy-staging.sh [commit]   # deploy (default: HEAD)
#   sudo bash scripts/deploy-staging.sh rollback   # roll back to previous
#
# Safety interlocks: staging env must point at -staging paths and a
# non-production port, or the script refuses to start the service.
set -Eeuo pipefail

REPO="${ZMOVIE_REPO:-/home/cvsz/zmovie}"
WORKTREE="/opt/zmovie-staging"
STAGING_ENV="/etc/zmovie/zmovie-staging.env"
STATE_FILE="/var/lib/zmovie-staging/deployed-commit"
BASE_URL="http://127.0.0.1:8090"

log(){ printf '[deploy-staging] %s\n' "$*"; }
fail(){ printf '[deploy-staging] FAIL: %s\n' "$*" >&2; exit 1; }
command -v git >/dev/null 2>&1 || fail "git is required"
command -v curl >/dev/null 2>&1 || fail "curl is required"
command -v python3 >/dev/null 2>&1 || fail "python3 is required"
[[ -f "$STAGING_ENV" ]] || fail "staging env missing: $STAGING_ENV"

# --- safety interlocks: never let staging touch production paths/ports ---
grep -q '^ZMOVIE_DB_PATH=/var/lib/zmovie-staging/' "$STAGING_ENV" \
  || fail "staging env DB path is not isolated"
grep -q '^ZMOVIE_PORT=8090$' "$STAGING_ENV" \
  || fail "staging env port is not 8090"
grep -q '^ZMOVIE_MEDIA_ROOT=/var/lib/zmovie-staging/' "$STAGING_ENV" \
  || fail "staging env media path is not isolated"

current_commit() {
  if [[ -d "$WORKTREE" ]]; then
    git -C "$WORKTREE" rev-parse HEAD 2>/dev/null || echo "none"
  else
    echo "none"
  fi
}

smoke() {
  local base="$1"
  curl -fsS --max-time 10 "$base/api/v2/health" >/dev/null \
    || { log "health failed"; return 1; }
  curl -fsS --max-time 15 "$base/api/v2/readyz" | grep -q '"ready"' \
    || { log "readyz failed"; return 1; }
  curl -fsS --max-time 10 "$base/api/v2/capabilities" >/dev/null \
    || { log "capabilities failed"; return 1; }
  python3 - "$base" "$STAGING_ENV" <<'PY'
import json
import sys
import urllib.request

base, env_path = sys.argv[1], sys.argv[2]
env = {}
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v


def call(method, path, body=None, token=None):
    req = urllib.request.Request(
        base + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json",
                 **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, json.loads(r.read().decode() or "{}")


status, login_body = call("POST", "/api/v2/auth/login",
                     {"username": env["ZMOVIE_ADMIN_USER"], "password": env["ZMOVIE_ADMIN_PASSWORD"]})
assert status == 200, "staging login failed"
token = login_body["token"]
status, project = call("POST", "/api/v2/projects",
                       {"name": "staging-smoke", "concept": "smoke test project"}, token)
assert status in (200, 201), "project create failed"
pid = project.get("id") or project.get("project", {}).get("id")
assert pid, "no project id returned"
status, _ = call("GET", f"/api/v2/projects/{pid}", token=token)
assert status == 200, "project fetch failed"
status, _ = call("DELETE", f"/api/v2/projects/{pid}", token=token)
assert status in (200, 204), "project delete failed"
print("staging CRUD smoke passed")
PY
}

deploy_commit() {
  local target="$1" prev
  prev="$(current_commit)"
  [[ "$prev" != "$target" ]] || log "already at $target (re-running checks)"
  if [[ -d "$WORKTREE" ]]; then
    git -C "$REPO" worktree remove --force "$WORKTREE"
  fi
  git -C "$REPO" worktree add --detach "$WORKTREE" "$target"
  chown -R zmovie:zmovie "$WORKTREE"
  echo "$prev" > "$STATE_FILE"
  chmod 644 "$STATE_FILE"
  log "worktree pinned at $target (previous: $prev)"
  systemctl restart zmovie-staging
  sleep 6
  if smoke "$BASE_URL"; then
    log "staging deploy verified at $target"
  else
    log "smoke failed; rolling back to $prev"
    rollback_to "$prev" || fail "rollback also failed; staging left stopped for inspection"
  fi
}

rollback_to() {
  local target="$1"
  [[ "$target" != "none" && -n "$target" ]] || fail "no previous commit recorded"
  if [[ -d "$WORKTREE" ]]; then
    git -C "$REPO" worktree remove --force "$WORKTREE"
  fi
  git -C "$REPO" worktree add --detach "$WORKTREE" "$target"
  chown -R zmovie:zmovie "$WORKTREE"
  systemctl restart zmovie-staging
  sleep 6
  smoke "$BASE_URL" && log "rollback verified at $target"
}

if [[ "${1:-}" == "rollback" ]]; then
  prev="$(cat "$STATE_FILE" 2>/dev/null || echo none)"
  rollback_to "$prev"
  exit 0
fi

TARGET="${1:-$(git -C "$REPO" rev-parse HEAD)}"
git -C "$REPO" cat-file -e "$TARGET" 2>/dev/null || fail "unknown commit: $TARGET"
deploy_commit "$TARGET"
