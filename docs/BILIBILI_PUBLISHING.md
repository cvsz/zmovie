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

## One-time Google login

Install dependencies and the browser if you are not using the automated installer:

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Open the interactive login flow on a GUI host:

```bash
python -m zmovie_platform.publishers.bilibili_hardened login
```

The browser opens Creator Center and attempts to surface the Google login option. Complete Google authentication and any 2FA yourself, then return to the terminal and press Enter. The saved state defaults to:

```text
data/bilibili/storage_state.json
```

Treat this file like a credential. It is stored under `data/`, which is ignored by Git, and should be readable only by the zMovie runtime account.

For a remote/headless server, perform the login on a GUI machine and securely copy `storage_state.json` to the path configured by `ZMOVIE_BILIBILI_STATE_PATH` (native installer default: `/var/lib/zmovie/bilibili/storage_state.json`).

After copying it, validate the session from the zMovie host:

```bash
python -m zmovie_platform.publishers.bilibili_hardened session
```

`configured=true` only means the state file exists. For a usable session the live probe must also return `authenticated=true`.

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

The API now probes the saved browser state before a real publish queue request. A stale or unauthenticated state file is rejected instead of being treated as ready.

The Studio UI exposes the same approval boundary. `Publish` is unavailable until a job has been explicitly approved, and a `submitted` job is labelled as not yet independently confirmed public.

## Docker

The zMovie image includes headless Chromium. The first Google login is best performed on a GUI checkout. Copy the resulting state file into the Docker data volume at:

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
- Treat `configured=true` and `authenticated=true` as separate conditions.
- If the Creator Center session is revoked, run the interactive login again.
- Treat `submitted` as a remote-confirmation boundary, not as proof of public visibility.
- If Bilibili changes its form, use a headed publish run and the generated `publish-error.png` to update selectors.
