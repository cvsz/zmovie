# Bilibili production completion gate

Status: **ACTIVE / finish before YouTube work**

This document defines the evidence required before zMovie calls the Bilibili publisher production-complete.

## Already verified

- publication package generation;
- final-video selection;
- generated 1280x720 cover;
- metadata/tag limits and AI disclosure;
- durable `prepared` publish jobs;
- explicit approval gate;
- hidden file-input support;
- conservative `submitted` vs `published` state semantics;
- live session probing;
- capture from an existing Chrome session through localhost CDP;
- Bilibili-only browser-state scoping so unrelated Google/Gmail/GitHub/etc. credentials are not copied to the server;
- live authenticated Creator Center session on native host `core` as the `zmovie` runtime user. See [`evidence/2026-09-09-core-bilibili-live-session.md`](evidence/2026-09-09-core-bilibili-live-session.md).
- production browser-state scope + live-auth verification on `core`: 13 Bilibili cookies, 1 Bilibili origin, no unexpected cookie domains/origins, and `authenticated=true`. See [`evidence/2026-09-09-core-bilibili-scope-auth-verified.md`](evidence/2026-09-09-core-bilibili-scope-auth-verified.md).

## Production session installation

On the GUI Chrome host, keep `https://studio.bilibili.tv/` authenticated and enable Chrome remote debugging locally. Capture with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\capture-bilibili-session.ps1
```

Current capture writes a least-privilege state containing only Bilibili cookies/origin storage.

Copy that state file to the native zMovie host, then install transactionally:

```bash
sudo bash /opt/zmovie/scripts/install-bilibili-session.sh /home/cvsz/storage_state.json
```

The installer:

1. verifies the installed Python publisher exposes the required `sanitize-state` capability before touching the current state;
2. sanitizes the input again to Bilibili-only state;
3. preserves the existing state for rollback;
4. installs the new state as the `zmovie` user with mode `0600`;
5. uses the production Playwright browser path;
6. performs a live Creator Center probe;
7. restores the previous state automatically if the live probe fails.

A partial/version-skew deployment fails closed before modifying an existing authenticated session. Upgrade the native installation before retrying the transactional installer.

PASS requires:

```json
{
  "configured": true,
  "checked": true,
  "authenticated": true
}
```

After installation or after an already-working state is present, verify both state scope and live authentication without printing cookie values:

```bash
sudo bash /opt/zmovie/scripts/verify-bilibili-session.sh
```

After a successful install, remove any temporary transfer copy and disable Chrome remote debugging on the GUI host.

## Controlled real-publication gate

Do **not** use the mock smoke project for a real upload.

Production completion requires one operator-approved project with a real final video. The required sequence is:

```text
real final movie
  -> prepare
  -> human review
  -> approve
  -> session live probe
  -> upload/submit
  -> durable submitted state
  -> remote/public URL confirmation
```

Commands on the native host must load `/etc/zmovie/zmovie.env` and use `/opt/zmovie/.venv/bin/python`.

Prepare:

```bash
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a; source /etc/zmovie/zmovie.env; set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened prepare --project PROJECT_ID
'
```

Review the exact title, description, tags, cover, type and schedule before approving:

```bash
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a; source /etc/zmovie/zmovie.env; set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened approve --job PUB_JOB_ID
'
```

Publish only after explicit operator approval:

```bash
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a; source /etc/zmovie/zmovie.env; set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened publish --job PUB_JOB_ID
'
```

Inspect durable state:

```bash
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a; source /etc/zmovie/zmovie.env; set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened status --job PUB_JOB_ID
'
```

A successful form interaction may end as `submitted`. That is **not** proof of public visibility. Production-complete requires a confirmed public Bilibili video URL and `remote_confirmation=true`.

## Completion definition

Bilibili is complete only when all of these are evidenced:

- [x] production browser state verified with Bilibili-only scope on `core`;
- [x] live Creator Center probe returns `authenticated=true` on `core`;
- [ ] real non-mock video package prepared;
- [ ] exact publication package explicitly approved;
- [ ] real upload submitted without automation error;
- [ ] Creator Center/public URL remotely confirmed;
- [ ] durable job state reflects the confirmed result;
- [ ] Chrome remote debugging disabled after session capture.

Until these boxes are evidenced, YouTube implementation remains deferred.
