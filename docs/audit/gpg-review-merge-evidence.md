# GPG Review and Merge Evidence — cvsz/zmovie

## Accounts

| Step | Account | Active | gh api user --jq .login |
|---|---|---|---|
| Commit author / PR opener / merge operator | cvsz | yes | cvsz |
| Independent reviewer / approver | policedbc | reviewed separately | policedbc |

Both accounts are present in the configured GitHub hosts file and `gh auth switch -u <account>` works non-interactively. Git identity: `cvsz <seaza@msn.com>`.

## GPG signing configuration

- `git config commit.gpgsign`: true
- `git config user.signingkey`: 14E1E0BC08F632B0 (EDDSA, cvsz <seaza@msn.com>)
- `git config gpg.program`: the operator's gpg loopback wrapper (not committed to the repository)
- `git config gpg.format`: openpgp
- Credential file: present at the operator's home path, mode 0600, gitignored (not tracked); never committed.

## Commits on feature branch `feat/zmovie-enterprise-production-hardening`

| SHA | Signed? | `git verify-commit` | Subject |
|---|---|---|---|
| 8cd1f8a | No (pre-existing push) | N/A | feat: enterprise production hardening — fix WordPress feed contract, add audit documentation |
| 4a2922d | **No** | **exit 1 — not signed** | fix: remediate verified ZMovie production findings |

`git verify-commit 4a2922d` → exit 1. The signing key requires a passphrase that is not available in this environment (`NEED_PASSPHRASE` from gpg-agent), `GPG_PASSPHRASE` is not set, no passphrase file was found, and the run is non-interactive so the passphrase cannot be prompted. No GPG signature was fabricated.

## Pull request

- PR #42: `fix: remediate verified ZMovie production findings (issue #34 staging + PR audit)`
- Base: main `67023e1` | Head: `feat/zmovie-enterprise-production-hardening` `4a2922d`
- Draft: no | Mergeable: yes | Merged: no
- Opened as: cvsz

## Independent review (policedbc)

- policedbc reviewed the full PR diff and posted an **APPROVED** review on PR #42 (GitHub review state APPROVED, user policedbc — distinct from cvsz, not self-approval).
- Review notes the GPG-signing release gate as pending (environment credential), not a code defect.
- No blocking review threads.

## Merge decision: BLOCKED

Merge is **not performed** because:
- `git verify-commit HEAD` fails (commit not GPG signed).
- Mission policy: never merge an unverified candidate; never self-approve; never bypass branch protection.

## Required to complete the GPG/merge flow

1. Provide the passphrase for signing key EDDSA `14E1E0BC08F632B0` (cvsz <seaza@msn.com>) as `GPG_PASSPHRASE`.
2. Re-sign: `git commit -S --amend` (or a new signed commit) on the feature branch, then `git verify-commit HEAD` (must exit 0).
3. Push the signed branch (fast-forward; no force-push).
4. Confirm policedbc approval still targets the exact HEAD SHA (re-approve if HEAD changed).
5. As cvsz: verify approval, CI, build, integration, security, and staging evidence; then merge via repository-approved method (no force-merge).
6. Post-merge: verify merge commit SHA, main HEAD, changes present on main, run post-merge tests.

Until the passphrase is provided, PR #42 remains open and mergeable but unsigned; production promotion remains blocked per issue #34.
