# core Bilibili live-session evidence — 2026-09-09

Host: `core`

## Verified observation

The native zMovie runtime account executed the hardened Bilibili session probe with the production environment loaded from `/etc/zmovie/zmovie.env` and the application virtualenv under `/opt/zmovie/.venv`.

Observed result:

```json
{
  "configured": true,
  "authenticated": true,
  "checked": true,
  "state_path": "/var/lib/zmovie/bilibili/storage_state.json",
  "headless": true,
  "studio_url": "https://studio.bilibili.tv/",
  "last_page_url": "https://studio.bilibili.tv/"
}
```

## What this proves

- the production state file exists at the configured native path;
- Playwright can launch in the production headless runtime;
- the `zmovie` service account can read/use the state;
- Creator Center is reachable from `core`;
- the saved Bilibili session is live and authenticated.

## Boundary

This evidence does **not** by itself prove that the installed file contains only Bilibili-scoped cookies/origin storage. That scope is verified separately by `scripts/verify-bilibili-session.sh` after the production code is upgraded to a revision containing the session-scope hardening.

The production installation also exposed a revision-skew condition during a later session-install attempt: `scripts/install-bilibili-session.sh` expected the `sanitize-state` CLI command while the installed Python module did not yet provide it. The currently authenticated session remained usable. The installer now fails closed before touching the existing state when such a mismatch is detected.
