# Bilibili Creator Center publishing

zMovie can prepare and submit completed projects to `https://studio.bilibili.tv/` through Playwright browser automation.

The integration deliberately does **not** ask for or persist a Google password, recovery code, authenticator secret, or 2FA code. Google sign-in is completed manually once in a visible browser; zMovie saves Playwright browser session state and reuses that authenticated state for later headless uploads.

## Creator Center limits encoded by zMovie

The current Creator Center form supports:

- title: up to 100 characters;
- introduction: up to 2000 characters;
- cover: zMovie generates 1280×720, exceeding the documented 1152×648 minimum;
- tags: up to 10;
- type: `Original` or `Repost`;
- optional playlist;
- immediate or scheduled release;
- scheduled release validation: at least 2 hours in the future and no more than 15 days in the future.

Because Creator Center is a browser UI rather than a stable public upload API, selectors may change. On automation failure zMovie stores a diagnostic screenshot under the publish-job directory and records the error in the publish job.

## Job-state semantics

Publication states are intentionally conservative:

- `prepared`: metadata, final video, cover and manifest exist;
- `approved`: an operator explicitly approved that exact publication package;
- `uploading`: browser automation is actively uploading/submitting;
- `submitted`: Creator Center accepted the form interaction, but zMovie has not independently confirmed a public video URL or final moderation state;
- `published`: zMovie observed a concrete Bilibili public video URL;
- `failed`: the automation or Creator Center reported a failure.

A successful button click is **not** treated as proof that a video is publicly visible.

## Reuse an already-open Chrome session

This is the preferred path when Chrome on a GUI workstation is already signed in to Google/Bilibili. zMovie can attach to that existing Chromium context over the Chrome DevTools Protocol (CDP) and snapshot the authenticated storage state without launching another browser.

On Chrome 144 or newer, in the **same Chrome window/profile you want to reuse**:

1. Open `chrome://inspect/#remote-debugging`.
2. Enable remote debugging.
3. Keep Chrome open.
4. Approve Chrome's incoming debugging-connection prompt when the zMovie capture command runs.
5. Make sure `https://studio.bilibili.tv/` is already signed in in that profile.

On Windows, from a normal zMovie checkout in your user directory, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\capture-bilibili-session.ps1
```

The helper creates/uses the checkout `.venv`, installs Python dependencies, discovers Chrome's local `DevToolsActivePort`, attaches to the existing Chrome context, verifies Creator Center authentication, and writes:

```text
%USERPROFILE%\storage_state.json
```

Equivalent direct command:

```powershell
.\.venv\Scripts\python.exe `
  -m zmovie_platform.publishers.bilibili_hardened capture-chrome `
  --state "$HOME\storage_state.json"
```

The default Windows Chrome user-data directory is auto-detected from `%LOCALAPPDATA%\Google\Chrome\User Data`. You can override discovery with:

```powershell
.\.venv\Scripts\python.exe `
  -m zmovie_platform.publishers.bilibili_hardened capture-chrome `
  --state "$HOME\storage_state.json" `
  --user-data-dir "D:\ChromeProfile\User Data"
```

Or attach to an explicitly known **local** CDP websocket endpoint:

```powershell
.\.venv\Scripts\python.exe `
  -m zmovie_platform.publishers.bilibili_hardened capture-chrome `
  --state "$HOME\storage_state.json" `
  --cdp-endpoint "ws://127.0.0.1:9222/devtools/browser/..."
```

Do not expose Chrome's debugging endpoint to the LAN or Internet. Run the capture helper on the same Windows machine as Chrome and copy only the resulting `storage_state.json` to the zMovie server.

The capture includes cookies, local storage and IndexedDB because authentication providers can store session material in more than one browser storage mechanism. zMovie does not capture real passkeys or ask for the Google password/2FA secret.

## One-time Google login in a new Playwright browser

Use this fallback only when you cannot reuse an existing Chrome profile. The login command requires a **visible GUI display**. A headless server with an empty `DISPLAY`/`WAYLAND_DISPLAY` cannot perform this interactive authentication. `xvfb-run` alone is not sufficient because the operator must see and complete Google sign-in and any 2FA challenges.

On a GUI checkout, install dependencies and Chromium if needed:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
```

Open the interactive login flow:

```bash
.venv/bin/python -m zmovie_platform.publishers.bilibili_hardened login \
  --state "$HOME/storage_state.json"
```

The browser opens Creator Center and attempts to surface the Google login option. Complete Google authentication and any 2FA yourself, then return to the terminal and press Enter.

Treat `storage_state.json` like a credential. Do not commit it, paste it into chat, or make it world-readable.

For a remote/headless native server, securely copy the generated state file to the path configured by `ZMOVIE_BILIBILI_STATE_PATH` (installer default: `/var/lib/zmovie/bilibili/storage_state.json`) and set ownership/permissions:

```bash
sudo install -d -o zmovie -g zmovie -m 0700 /var/lib/zmovie/bilibili
sudo install -o zmovie -g zmovie -m 0600 "$HOME/storage_state.json" /var/lib/zmovie/bilibili/storage_state.json
```

## Native production host commands

Do not clone another working tree under `/opt/zmovie`; that directory is the installed production application and is normally root-owned.

When running the CLI manually on a native install, use the application's virtualenv **and load the production environment first**. Otherwise the module defaults to relative development paths such as `/opt/zmovie/data/bilibili/storage_state.json` instead of the native installer path under `/var/lib/zmovie`.

Validate the production session as the runtime user:

```bash
sudo -u zmovie bash -lc '
cd /opt/zmovie
set -a
source /etc/zmovie/zmovie.env
set +a
exec .venv/bin/python -m zmovie_platform.publishers.bilibili_hardened session
'
```

`configured=true` only means the state file exists. A usable session requires the live probe to return both `checked=true` and `authenticated=true`.

## CLI workflow

A project must have a final/assembled video asset first.

Prepare title, description, tags and cover:

```bash
python -m zmovie_platform.publishers.bilibili_hardened prepare --project PROJECT_ID
```

Optional metadata:

```bash
python -m zmovie_platform.publishers.bilibili_hardened prepare \
  --project PROJECT_ID \
  --playlist "AI Movies" \
  --type Original \
  --schedule-at "2026-09-09T22:30:00+07:00"
```

Review the returned package, then approve it:

```bash
python -m zmovie_platform.publishers.bilibili_hardened approve --job PUB_JOB_ID
```

Before a real upload, validate the session:

```bash
python -m zmovie_platform.publishers.bilibili_hardened session
```

Publish headlessly:

```bash
python -m zmovie_platform.publishers.bilibili_hardened publish --job PUB_JOB_ID
```

For debugging a Creator Center UI change, run the actual upload with a visible browser:

```bash
python -m zmovie_platform.publishers.bilibili_hardened publish --job PUB_JOB_ID --headed
```

Inspect the durable state afterward:

```bash
python -m zmovie_platform.publishers.bilibili_hardened status --job PUB_JOB_ID
```

## API workflow

```text
POST /api/v2/projects/{project_id}/publish/bilibili/prepare
POST /api/v2/publish/jobs/{job_id}/approve
POST /api/v2/publish/jobs/{job_id}/publish
GET  /api/v2/publish/jobs/{job_id}
GET  /api/v2/publish/jobs?project_id={project_id}
GET  /api/v2/publish/bilibili/session
```

The API probes the saved browser state before a real publish queue request. A stale or unauthenticated state file is rejected instead of being treated as ready.

The Studio UI exposes the same approval boundary. `Publish` is unavailable until a job has been explicitly approved, and a `submitted` job is labelled as not yet independently confirmed public.

## Docker

The zMovie image includes headless Chromium. The first Google login or existing-Chrome capture is best performed on a GUI workstation. Copy the resulting state file into the Docker data volume at:

```text
/app/data/bilibili/storage_state.json
```

The container then validates and reuses that state for headless publish jobs.

## AI disclosure

Default metadata includes a transparent statement that the video contains AI-generated/synthetic visual content and was created with zMovie / an AI-video workflow such as ComfyUI. Review this text before approval and adjust it to the content and applicable platform requirements.

## Operational safety

- Keep `ZMOVIE_BILIBILI_AUTO_PUBLISH=false` unless you intentionally want prepared jobs auto-approved.
- Do not commit browser state/cookies.
- Do not share the state file.
- Do not expose a Chrome remote-debugging endpoint to the LAN or Internet; perform capture locally on the Chrome workstation.
- Treat `configured=true` and `authenticated=true` as separate conditions.
- If the Creator Center session is revoked, capture/login again on a visible GUI host.
- Treat `submitted` as a remote-confirmation boundary, not as proof of public visibility.
- If Bilibili changes its form, use a headed publish run on a GUI host and the generated `publish-error.png` to update selectors.
