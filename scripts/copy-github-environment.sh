#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE_REPO="${SOURCE_REPO:-cvsz/zeaz-web}"
TARGET_REPO="${TARGET_REPO:-}"
ENVIRONMENT="${ENVIRONMENT:-production}"
COPY_VARIABLES="${COPY_VARIABLES:-true}"
REPLACE_BRANCH_POLICIES="${REPLACE_BRANCH_POLICIES:-true}"

log(){ printf '[zMovie GitHub env] %s\n' "$*"; }
fail(){ printf '[zMovie GitHub env] ERROR: %s\n' "$*" >&2; exit 1; }

command -v gh >/dev/null 2>&1 || fail "GitHub CLI (gh) is required"
command -v jq >/dev/null 2>&1 || fail "jq is required"
gh auth status >/dev/null 2>&1 || fail "gh is not authenticated"

if [[ -z "$TARGET_REPO" ]]; then
  TARGET_REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)"
fi
[[ -n "$TARGET_REPO" ]] || fail "set TARGET_REPO=owner/repo or run inside a GitHub checkout"

urlencode(){ jq -rn --arg v "$1" '$v|@uri'; }
ENV_ENC="$(urlencode "$ENVIRONMENT")"

log "source: $SOURCE_REPO / $ENVIRONMENT"
log "target: $TARGET_REPO / $ENVIRONMENT"

source_env="$(gh api "repos/$SOURCE_REPO/environments/$ENV_ENC")"

wait_timer="$(jq '[.protection_rules[]? | select(.type=="wait_timer") | .wait_timer][0] // 0' <<<"$source_env")"
prevent_self_review="$(jq '[.protection_rules[]? | select(.type=="required_reviewers") | .prevent_self_review][0] // false' <<<"$source_env")"
reviewers="$(jq '[.protection_rules[]? | select(.type=="required_reviewers") | .reviewers[]? | {type:.type,id:.reviewer.id}]' <<<"$source_env")"
branch_policy="$(jq '.deployment_branch_policy // null' <<<"$source_env")"

payload="$(jq -n \
  --argjson wait_timer "$wait_timer" \
  --argjson prevent_self_review "$prevent_self_review" \
  --argjson reviewers "$reviewers" \
  --argjson deployment_branch_policy "$branch_policy" \
  '{wait_timer:$wait_timer,prevent_self_review:$prevent_self_review,reviewers:$reviewers,deployment_branch_policy:$deployment_branch_policy}')"

gh api --method PUT "repos/$TARGET_REPO/environments/$ENV_ENC" --input - <<<"$payload" >/dev/null
log "copied environment protection rules"

custom_policies="$(jq -r '.deployment_branch_policy.custom_branch_policies // false' <<<"$source_env")"
if [[ "$custom_policies" == "true" ]]; then
  src_policies="$(gh api --paginate "repos/$SOURCE_REPO/environments/$ENV_ENC/deployment-branch-policies?per_page=100" --jq '.branch_policies[]? | {name,type}')"
  tgt_json="$(gh api --paginate "repos/$TARGET_REPO/environments/$ENV_ENC/deployment-branch-policies?per_page=100" 2>/dev/null || printf '{"branch_policies":[]}')"

  if [[ "$REPLACE_BRANCH_POLICIES" == "true" ]]; then
    jq -r '.branch_policies[]?.id' <<<"$tgt_json" | while read -r policy_id; do
      [[ -n "$policy_id" ]] || continue
      gh api --method DELETE "repos/$TARGET_REPO/environments/$ENV_ENC/deployment-branch-policies/$policy_id" >/dev/null
    done
  fi

  if [[ -n "$src_policies" ]]; then
    while IFS= read -r policy; do
      [[ -n "$policy" ]] || continue
      gh api --method POST "repos/$TARGET_REPO/environments/$ENV_ENC/deployment-branch-policies" --input - <<<"$policy" >/dev/null
    done <<<"$src_policies"
  fi
  log "copied custom deployment branch policies"
fi

if [[ "$COPY_VARIABLES" == "true" ]]; then
  variables="$(gh api --paginate "repos/$SOURCE_REPO/environments/$ENV_ENC/variables?per_page=100" --jq '.variables[]? | {name,value}' 2>/dev/null || true)"
  if [[ -n "$variables" ]]; then
    while IFS= read -r variable; do
      [[ -n "$variable" ]] || continue
      name="$(jq -r '.name' <<<"$variable")"
      value="$(jq -r '.value' <<<"$variable")"
      if gh api "repos/$TARGET_REPO/environments/$ENV_ENC/variables/$name" >/dev/null 2>&1; then
        jq -n --arg name "$name" --arg value "$value" '{name:$name,value:$value}' \
          | gh api --method PATCH "repos/$TARGET_REPO/environments/$ENV_ENC/variables/$name" --input - >/dev/null
      else
        jq -n --arg name "$name" --arg value "$value" '{name:$name,value:$value}' \
          | gh api --method POST "repos/$TARGET_REPO/environments/$ENV_ENC/variables" --input - >/dev/null
      fi
    done <<<"$variables"
    log "copied environment variables"
  else
    log "no environment variables found or variables endpoint is unavailable"
  fi
fi

secret_names="$(gh api --paginate "repos/$SOURCE_REPO/environments/$ENV_ENC/secrets?per_page=100" --jq '.secrets[]?.name' 2>/dev/null || true)"
if [[ -n "$secret_names" ]]; then
  log "secret VALUES cannot be exported by GitHub; configure these names securely in the target environment:"
  while IFS= read -r name; do printf '  - %s\n' "$name"; done <<<"$secret_names"
else
  log "no readable environment secret metadata found"
fi

log "PASS: copied all GitHub environment settings that GitHub permits to be exported"
