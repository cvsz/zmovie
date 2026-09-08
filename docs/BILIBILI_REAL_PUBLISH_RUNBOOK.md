# Bilibili controlled real-publication runbook

Status: **ACTIVE — final external publication gate before YouTube work**

This runbook is for the first real, non-mock Bilibili publication from the native zMovie host.

## Preconditions

All of these must be true before upload:

- zMovie native service is healthy;
- production Bilibili browser state exists at the configured `ZMOVIE_BILIBILI_STATE_PATH`;
- `scripts/verify-bilibili-session.sh` passes Bilibili-only scope and live authentication;
- the project is a real project, not the smoke project used for integration evidence;
- the project has a real final/assembled video asset;
- title, description, tags, content type, cover, subtitle and release timing have been reviewed by an operator;
- `ZMOVIE_BILIBILI_AUTO_PUBLISH=false` remains the default.

## 1. Upgrade the native install atomically

```bash
curl -fsSL https://raw.githubusercontent.com/cvsz/zmovie/main/install.sh \
  | sudo bash -s -- upgrade
```

## 2. Verify the production browser state

```bash
sudo bash /opt/zmovie/scripts/verify-bilibili-session.sh
```

PASS requires:

```text
scope = bilibili_only
unexpected_cookie_domains = []
unexpected_origins = []
configured = true
checked = true
authenticated = true
```

Do not continue if this gate fails.

## 3. Prepare a real publication package

```bash
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a; source /etc/zmovie/zmovie.env; set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened prepare --project PROJECT_ID
'
```

Record the returned `PUB_JOB_ID`.

Review the exact package before approval:

```bash
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a; source /etc/zmovie/zmovie.env; set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened status --job PUB_JOB_ID
'
```

Expected state: `prepared`.

## 4. Approve the exact package

Only after human review:

```bash
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a; source /etc/zmovie/zmovie.env; set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened approve --job PUB_JOB_ID
'
```

Expected state: `approved`.

## 5. Submit the upload

```bash
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a; source /etc/zmovie/zmovie.env; set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened publish --job PUB_JOB_ID
'
```

A successful form interaction is expected to finish as `submitted` unless zMovie immediately observes a concrete public Bilibili video URL. `submitted` is not proof of public visibility.

Inspect durable state:

```bash
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a; source /etc/zmovie/zmovie.env; set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened status --job PUB_JOB_ID
'
```

If automation fails, inspect the durable error and the `publish-error.png` diagnostic in that job's publish directory. Do not blindly retry if Creator Center may already have accepted the upload.

## 6. Confirm the public URL

When Creator Center exposes the final public video URL, confirm it through the production host:

```bash
sudo bash /opt/zmovie/scripts/confirm-bilibili-publication.sh \
  PUB_JOB_ID \
  'https://www.bilibili.tv/video/...'
```

The confirmation helper:

1. requires an HTTPS `bilibili.tv` `/video/` URL;
2. opens the URL with the production Playwright runtime;
3. rejects redirects outside a Bilibili video page;
4. rejects HTTP 4xx/5xx responses and obvious unavailable/not-found pages;
5. records `remote_confirmation=true` only after the live probe passes;
6. updates durable job state to `published` and stores the confirmed URL.

Final status:

```bash
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a; source /etc/zmovie/zmovie.env; set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened status --job PUB_JOB_ID
'
```

Production-complete requires:

```text
status = published
published_url = https://...bilibili.tv/.../video/...
metadata.remote_confirmation = true
```

## 7. Close temporary access paths

After the session has been captured and verified:

- disable Chrome remote debugging on the GUI Windows host;
- remove temporary transferred browser-state files from user home directories;
- retain only the production Bilibili-only state owned by `zmovie` with mode `0600`;
- do not commit browser-state files, screenshots containing sensitive data, or operator credentials.

## Completion boundary

Bilibili is not considered complete until a real non-mock publication reaches durable `published` state with `remote_confirmation=true` and a confirmed public URL. YouTube implementation remains deferred until that evidence exists.
