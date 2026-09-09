# zMovie release and synchronization guide

This project uses evidence-backed releases. A signed commit, a green local
suite, hosted CI, deployment health, and external publication are separate
claims that must not be conflated.

## Prepare the change

Before committing, inspect the complete diff and scope:

```bash
git status --short --branch
git diff --check
git diff --stat
git diff --name-only
```

Do not stage `.env*`, credentials, browser storage, generated caches,
databases, media, private host paths, or unrelated worktree changes.

## Sign commits

Use the configured project identity and verify every new commit:

```bash
git commit --gpg-sign=220A4C8CCC7D2D50 -m "docs: describe the release boundary"
git verify-commit HEAD
git log --show-signature -1
```

Do not rewrite historic unsigned commits merely to change their signature.

## Verify before push

Run the relevant local checks, including:

```bash
python3 scripts/verify_docs.py
git diff --check
make check
docker compose config --quiet
```

Use the isolated declared dependency environment when the system interpreter
does not provide the project requirements. Record unavailable checks and their
reason.

## Synchronize remote state

Fetch before comparing refs and avoid an ambient invalid token overriding the
stored GitHub authentication:

```bash
env -u GITHUB_TOKEN git fetch origin
git rev-parse HEAD origin/main
git log --oneline origin/main..HEAD
git log --oneline HEAD..origin/main
```

If `origin/main` moved, stop and reconcile the branch with review. Never
force-push to bypass remote history or required checks. Use a topic branch and
pull request when direct main updates are protected.

## Hosted and runtime evidence

After a push, verify GitHub Actions for the exact pushed SHA. Separately verify
the deployed service, public health/Studio routes, renderer output, and any
external publication confirmation. A deployment badge or generated release
note is not a substitute for the underlying observation.

## Rollback

Prefer a new corrective commit or a reviewed revert. Preserve the failed
artifact, logs, and exact SHA for diagnosis. Restore persistent data only from a
known backup after stopping the service and validating the target state.
