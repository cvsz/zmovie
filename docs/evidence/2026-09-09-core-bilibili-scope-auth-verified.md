# Bilibili production browser-state scope + live-auth evidence

Date: 2026-09-09 (Asia/Bangkok)
Host: `core`
Runtime user: `zmovie`

## Operator command

```bash
sudo bash /opt/zmovie/scripts/verify-bilibili-session.sh
```

## Observed scope result

```json
{
  "scope": "bilibili_only",
  "cookies": 13,
  "origins": 1,
  "unexpected_cookie_domains": [],
  "unexpected_origins": []
}
```

No cookie values or session tokens were recorded in this evidence file.

## Observed live Creator Center probe

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

Verifier result:

```text
PASS: Bilibili-only state scope and live authenticated Creator Center session verified
```

## Evidence boundary

This closes the production browser-state scope gate and the live-authentication gate. It does not prove a real upload, moderation acceptance, public visibility, or remote publication confirmation. Those remain separate completion gates.
