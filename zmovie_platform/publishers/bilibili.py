from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..models import Project, utcnow
from ..repository import get_project, list_assets
from ..storage import connect, dumps, loads

STUDIO_URL = os.getenv("ZMOVIE_BILIBILI_STUDIO_URL", "https://studio.bilibili.tv/").strip()
PUBLISH_ROOT = Path(os.getenv("ZMOVIE_PUBLISH_ROOT", "data/publish"))
STATE_PATH = Path(os.getenv("ZMOVIE_BILIBILI_STATE_PATH", "data/bilibili/storage_state.json"))
HEADLESS = os.getenv("ZMOVIE_BILIBILI_HEADLESS", "true").lower() not in {"0", "false", "no", "off"}
AUTO_PUBLISH = os.getenv("ZMOVIE_BILIBILI_AUTO_PUBLISH", "false").lower() in {"1", "true", "yes", "on"}
BROWSER_CHANNEL = os.getenv("ZMOVIE_BILIBILI_BROWSER_CHANNEL", "").strip()
TIMEOUT_MS = int(os.getenv("ZMOVIE_BILIBILI_TIMEOUT_MS", "120000"))

TITLE_MAX = 100
DESCRIPTION_MAX = 2000
TAG_MAX = 10
MIN_SCHEDULE = timedelta(hours=2)
MAX_SCHEDULE = timedelta(days=15)


@dataclass(frozen=True)
class PublicationPackage:
    project_id: str
    video_path: str
    cover_path: str
    title: str
    description: str
    tags: list[str]
    playlist: str = ""
    content_type: str = "Original"
    schedule_at: str = ""
    subtitle_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _truncate(text: str, maximum: int) -> str:
    return text.strip()[:maximum]


def _dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        clean = " ".join(str(item).strip().split())
        key = clean.casefold()
        if clean and key not in seen:
            seen.add(key)
            out.append(clean)
    return out


def _validate_schedule(value: str) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("schedule_at must be ISO-8601") from exc
    if dt.tzinfo is None:
        raise ValueError("schedule_at must include a timezone offset")
    dt_utc = dt.astimezone(timezone.utc)
    delta = dt_utc - _now()
    if delta < MIN_SCHEDULE:
        raise ValueError("Bilibili scheduled release must be at least 2 hours in the future")
    if delta > MAX_SCHEDULE:
        raise ValueError("Bilibili scheduled release must not be more than 15 days in the future")
    return dt_utc.isoformat()


def _pick_final_video(project_id: str) -> Path:
    candidates = list_assets(project_id, "final") + list_assets(project_id, "render")
    for asset in candidates:
        path = Path(str(asset.get("path", ""))).expanduser()
        if path.is_file() and path.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm", ".m4v"}:
            return path.resolve()
    raise FileNotFoundError("no assembled/final video asset found; assemble the project before publishing")


def _cover_from_video(video: Path, output: Path) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to generate a Bilibili cover")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-ss",
        "00:00:01",
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-vf",
        "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
        "-q:v",
        "2",
        str(output),
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=90, check=False)
    if proc.returncode != 0 or not output.is_file():
        raise RuntimeError(f"cover generation failed: {proc.stderr[-1000:]}")
    return output.resolve()


def build_metadata(project: Project) -> tuple[str, str, list[str]]:
    title = _truncate(project.name or "Untitled zMovie", TITLE_MAX)
    character_names = [character.name for character in project.characters if character.name]
    description_parts = [
        project.concept.strip(),
        f"Genre: {project.genre}. Visual style: {project.visual_style}.",
        "AI-generated/synthetic visual content created with zMovie and an AI video workflow such as ComfyUI.",
    ]
    description = _truncate("\n\n".join(part for part in description_parts if part), DESCRIPTION_MAX)
    tags = _dedupe([
        project.genre,
        "AI Video",
        "ComfyUI",
        "zMovie",
        "Cinematic",
        *character_names,
    ])[:TAG_MAX]
    return title, description, tags


def prepare_bilibili_publish(
    project_id: str,
    *,
    title: str = "",
    description: str = "",
    tags: list[str] | None = None,
    playlist: str = "",
    content_type: str = "Original",
    schedule_at: str = "",
    video_path: str = "",
    cover_path: str = "",
    subtitle_path: str = "",
) -> dict[str, Any]:
    project = get_project(project_id)
    if project is None:
        raise ValueError("project not found")
    default_title, default_description, default_tags = build_metadata(project)
    selected_video = Path(video_path).expanduser().resolve() if video_path else _pick_final_video(project_id)
    if not selected_video.is_file():
        raise FileNotFoundError(f"video not found: {selected_video}")

    job_id = f"pub_{uuid.uuid4().hex[:12]}"
    job_dir = PUBLISH_ROOT / project_id / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    if cover_path:
        selected_cover = Path(cover_path).expanduser().resolve()
        if not selected_cover.is_file():
            raise FileNotFoundError(f"cover not found: {selected_cover}")
    else:
        selected_cover = _cover_from_video(selected_video, job_dir / "cover-1280x720.jpg")

    selected_subtitle = ""
    if subtitle_path:
        subtitle = Path(subtitle_path).expanduser().resolve()
        if not subtitle.is_file():
            raise FileNotFoundError(f"subtitle not found: {subtitle}")
        if subtitle.suffix.lower() not in {".srt", ".vtt", ".ass"}:
            raise ValueError("subtitle must be .srt, .vtt or .ass")
        selected_subtitle = str(subtitle)

    normalized_type = content_type.strip().title()
    if normalized_type not in {"Original", "Repost"}:
        raise ValueError("content_type must be Original or Repost")
    normalized_schedule = _validate_schedule(schedule_at)
    final_title = _truncate(title or default_title, TITLE_MAX)
    final_description = _truncate(description or default_description, DESCRIPTION_MAX)
    final_tags = _dedupe(tags or default_tags)[:TAG_MAX]
    if not final_title:
        raise ValueError("title is required")

    package = PublicationPackage(
        project_id=project_id,
        video_path=str(selected_video),
        cover_path=str(selected_cover),
        title=final_title,
        description=final_description,
        tags=final_tags,
        playlist=playlist.strip(),
        content_type=normalized_type,
        schedule_at=normalized_schedule,
        subtitle_path=selected_subtitle,
    )
    now = utcnow()
    with connect() as conn:
        conn.execute(
            "INSERT INTO publish_jobs(id,project_id,platform,status,title,description,tags,video_path,cover_path,subtitle_path,playlist,content_type,schedule_at,metadata,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                job_id,
                project_id,
                "bilibili_tv",
                "prepared",
                package.title,
                package.description,
                dumps(package.tags),
                package.video_path,
                package.cover_path,
                package.subtitle_path,
                package.playlist,
                package.content_type,
                package.schedule_at,
                dumps({"approval_required": not AUTO_PUBLISH, "studio_url": STUDIO_URL}),
                now,
                now,
            ),
        )
    manifest = job_dir / "publication.json"
    manifest.write_text(json.dumps({"job_id": job_id, **package.to_dict()}, ensure_ascii=False, indent=2), encoding="utf-8")
    if AUTO_PUBLISH:
        approve_publish_job(job_id)
    return get_publish_job(job_id) or {}


def _decode_job(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["tags"] = loads(item.get("tags"), [])
    item["metadata"] = loads(item.get("metadata"), {})
    return item


def get_publish_job(job_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM publish_jobs WHERE id=?", (job_id,)).fetchone()
        return _decode_job(row) if row is not None else None


def list_publish_jobs(project_id: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 1000))
    with connect() as conn:
        if project_id:
            rows = conn.execute("SELECT * FROM publish_jobs WHERE project_id=? ORDER BY created_at DESC LIMIT ?", (project_id, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM publish_jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [_decode_job(row) for row in rows]


def _update_job(job_id: str, **fields: Any) -> dict[str, Any]:
    allowed = {"status", "published_url", "error", "metadata"}
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"unsupported publish-job fields: {sorted(unknown)}")
    if "metadata" in fields:
        fields["metadata"] = dumps(fields["metadata"])
    fields["updated_at"] = utcnow()
    assignments = ",".join(f"{key}=?" for key in fields)
    values = list(fields.values()) + [job_id]
    with connect() as conn:
        cur = conn.execute(f"UPDATE publish_jobs SET {assignments} WHERE id=?", values)
        if cur.rowcount == 0:
            raise ValueError("publish job not found")
    return get_publish_job(job_id) or {}


def approve_publish_job(job_id: str) -> dict[str, Any]:
    job = get_publish_job(job_id)
    if job is None:
        raise ValueError("publish job not found")
    if job["status"] not in {"prepared", "failed"}:
        raise ValueError(f"publish job cannot be approved from status {job['status']}")
    metadata = dict(job.get("metadata") or {})
    metadata["approved_at"] = utcnow()
    return _update_job(job_id, status="approved", error="", metadata=metadata)


def _playwright_import() -> Any:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is not installed. Run: pip install -r requirements.txt && python -m playwright install chromium") from exc
    return sync_playwright


def _browser_context(playwright: Any, *, headless: bool, state_path: Path | None = None) -> tuple[Any, Any]:
    launch: dict[str, Any] = {"headless": headless}
    if BROWSER_CHANNEL:
        launch["channel"] = BROWSER_CHANNEL
    browser = playwright.chromium.launch(**launch)
    kwargs: dict[str, Any] = {"viewport": {"width": 1440, "height": 1000}}
    if state_path and state_path.is_file():
        kwargs["storage_state"] = str(state_path)
    context = browser.new_context(**kwargs)
    context.set_default_timeout(TIMEOUT_MS)
    return browser, context


def _visible(locator: Any) -> bool:
    try:
        return locator.count() > 0 and locator.first.is_visible()
    except Exception:
        return False


def _logged_in(page: Any) -> bool:
    if "login" in page.url.lower():
        return False
    for text in ("My Videos", "Data Analysis", "Hi, creator!", "Playlists"):
        if _visible(page.get_by_text(text, exact=False)):
            return True
    if _visible(page.get_by_text("Log in", exact=False)) or _visible(page.get_by_text("Sign in", exact=False)):
        return False
    return "studio.bilibili.tv" in page.url


def interactive_google_login(state_path: Path = STATE_PATH) -> Path:
    sync_playwright = _playwright_import()
    state_path = state_path.expanduser().resolve()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, context = _browser_context(p, headless=False)
        page = context.new_page()
        page.goto(STUDIO_URL, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
        if not _logged_in(page):
            for label in ("Log in", "Sign in"):
                locator = page.get_by_text(label, exact=False)
                if _visible(locator):
                    try:
                        locator.first.click()
                        break
                    except Exception:
                        pass
            time.sleep(1)
            google = page.get_by_text("Google", exact=False)
            if _visible(google):
                try:
                    google.first.click()
                except Exception:
                    pass
        print("Complete Google sign-in in the opened browser. zMovie never asks for or stores your Google password.")
        input("After Creator Center is fully signed in, press Enter here to save the browser session: ")
        page.goto(STUDIO_URL, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
        if not _logged_in(page):
            browser.close()
            raise RuntimeError("Creator Center login was not detected; session was not saved")
        context.storage_state(path=str(state_path))
        try:
            state_path.chmod(0o600)
        except OSError:
            pass
        browser.close()
    return state_path


def _first(page: Any, selectors: list[str]) -> Any | None:
    for selector in selectors:
        try:
            locator = page.locator(selector)
            if locator.count() > 0 and locator.first.is_visible():
                return locator.first
        except Exception:
            continue
    return None


def _fill_required(page: Any, selectors: list[str], value: str, label: str) -> None:
    locator = _first(page, selectors)
    if locator is None:
        raise RuntimeError(f"could not locate Bilibili {label} field; Creator Center UI may have changed")
    locator.fill(value)


def _click_text(page: Any, values: list[str], *, required: bool = True) -> bool:
    for value in values:
        try:
            locator = page.get_by_text(value, exact=True)
            if locator.count() > 0 and locator.first.is_visible():
                locator.first.click()
                return True
        except Exception:
            continue
    if required:
        raise RuntimeError(f"could not locate Creator Center control: {values}")
    return False


def _open_upload(page: Any) -> None:
    page.goto(STUDIO_URL, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
    if not _logged_in(page):
        raise RuntimeError("Bilibili session is not authenticated; run the Google login command first")
    if _click_text(page, ["Upload"], required=False):
        page.wait_for_load_state("domcontentloaded")
    upload_url = os.getenv("ZMOVIE_BILIBILI_UPLOAD_URL", "").strip()
    if upload_url and "studio.bilibili.tv" in upload_url:
        page.goto(upload_url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)


def _set_video(page: Any, path: str) -> None:
    selectors = [
        "input[type=file][accept*='video']",
        "input[type=file][accept*='.mp4']",
        "input[type=file]",
    ]
    locator = _first(page, selectors)
    if locator is None:
        raise RuntimeError("could not locate Creator Center video file input")
    locator.set_input_files(path)


def _set_cover(page: Any, path: str) -> None:
    candidates = page.locator("input[type=file]")
    for index in range(candidates.count()):
        locator = candidates.nth(index)
        try:
            accept = (locator.get_attribute("accept") or "").lower()
            if "image" in accept or any(ext in accept for ext in (".jpg", ".jpeg", ".png", ".webp")):
                locator.set_input_files(path)
                return
        except Exception:
            continue
    if _click_text(page, ["Upload a cover"], required=False):
        time.sleep(0.5)
        candidates = page.locator("input[type=file]")
        for index in range(candidates.count() - 1, -1, -1):
            try:
                candidates.nth(index).set_input_files(path)
                return
            except Exception:
                continue
    raise RuntimeError("could not locate Creator Center cover upload control")


def _fill_tags(page: Any, tags: list[str]) -> None:
    if not tags:
        return
    locator = _first(page, [
        "input[placeholder*='tag' i]",
        "input[placeholder*='Tags' i]",
        "input[maxlength='20']",
    ])
    if locator is None:
        return
    for tag in tags[:TAG_MAX]:
        try:
            locator.fill(tag)
            locator.press("Enter")
        except Exception:
            break


def _select_playlist(page: Any, playlist: str) -> None:
    if not playlist:
        return
    if not _click_text(page, ["Please choose a playlist", "Select None"], required=False):
        raise RuntimeError("playlist requested but playlist selector was not found")
    option = page.get_by_text(playlist, exact=True)
    if not _visible(option):
        raise RuntimeError(f"playlist not found in Creator Center: {playlist}")
    option.first.click()


def _set_schedule(page: Any, schedule_at: str) -> None:
    if not schedule_at:
        _click_text(page, ["Release Now"], required=False)
        return
    _validate_schedule(schedule_at)
    _click_text(page, ["Scheduled Release"])
    dt = datetime.fromisoformat(schedule_at.replace("Z", "+00:00")).astimezone()
    combined = dt.strftime("%Y-%m-%d %H:%M")
    single = _first(page, ["input[type='datetime-local']", "input[placeholder*='date and time' i]"])
    if single is not None:
        single.fill(dt.strftime("%Y-%m-%dT%H:%M") if (single.get_attribute("type") or "") == "datetime-local" else combined)
        return
    date_inputs = page.locator("input")
    visible = [date_inputs.nth(i) for i in range(date_inputs.count()) if date_inputs.nth(i).is_visible()]
    date_like = [loc for loc in visible if "date" in ((loc.get_attribute("placeholder") or "").lower())]
    time_like = [loc for loc in visible if "time" in ((loc.get_attribute("placeholder") or "").lower())]
    if date_like and time_like:
        date_like[0].fill(dt.strftime("%Y-%m-%d"))
        time_like[0].fill(dt.strftime("%H:%M"))
        return
    raise RuntimeError("scheduled release requested but date/time controls were not recognized")


def _set_subtitle(page: Any, subtitle_path: str) -> bool:
    if not subtitle_path:
        return False
    if not _click_text(page, ["Add Subtitles", "+ Add Subtitles"], required=False):
        return False
    time.sleep(0.5)
    candidates = page.locator("input[type=file]")
    for index in range(candidates.count() - 1, -1, -1):
        locator = candidates.nth(index)
        accept = (locator.get_attribute("accept") or "").lower()
        if not accept or any(ext in accept for ext in (".srt", ".vtt", ".ass", "text")):
            try:
                locator.set_input_files(subtitle_path)
                return True
            except Exception:
                continue
    return False


def _submit_publication(page: Any) -> None:
    for value in ("Upload Now", "Publish", "Submit"):
        try:
            button = page.get_by_role("button", name=value, exact=True)
            if button.count() and button.first.is_visible():
                button.first.wait_for(state="visible", timeout=TIMEOUT_MS)
                button.first.click()
                return
        except Exception:
            pass
        try:
            text = page.get_by_text(value, exact=True)
            if text.count() and text.first.is_visible():
                text.first.click()
                return
        except Exception:
            pass
    raise RuntimeError("could not locate Creator Center publish/upload button")


def _automate_publish(job: dict[str, Any], *, headless: bool = HEADLESS, state_path: Path = STATE_PATH) -> dict[str, Any]:
    state_path = state_path.expanduser().resolve()
    if not state_path.is_file():
        raise RuntimeError(f"Bilibili browser session not found at {state_path}; run Google login first")
    sync_playwright = _playwright_import()
    screenshot_dir = PUBLISH_ROOT / str(job["project_id"]) / str(job["id"])
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, context = _browser_context(p, headless=headless, state_path=state_path)
        page = context.new_page()
        try:
            _open_upload(page)
            _set_video(page, str(job["video_path"]))
            # Wait for the metadata form to become interactive after upload initialization.
            page.wait_for_timeout(1500)
            _fill_required(page, ["input[maxlength='100']", "input[placeholder*='title' i]"], str(job["title"]), "title")
            _fill_required(page, ["textarea[maxlength='2000']", "textarea"], str(job["description"]), "introduction")
            _set_cover(page, str(job["cover_path"]))
            _click_text(page, [str(job["content_type"])], required=False)
            _select_playlist(page, str(job.get("playlist") or ""))
            _fill_tags(page, list(job.get("tags") or []))
            subtitle_uploaded = _set_subtitle(page, str(job.get("subtitle_path") or ""))
            _set_schedule(page, str(job.get("schedule_at") or ""))
            _submit_publication(page)
            # Allow Creator Center to process the submit and surface server-side validation.
            try:
                page.wait_for_load_state("networkidle", timeout=min(TIMEOUT_MS, 60000))
            except Exception:
                page.wait_for_timeout(4000)
            current_url = page.url
            body_text = ""
            try:
                body_text = page.locator("body").inner_text(timeout=5000)
            except Exception:
                pass
            lower = body_text.lower()
            if "invalid release time" in lower or "upload failed" in lower or "submission failed" in lower:
                raise RuntimeError("Creator Center reported a validation/upload failure")
            context.storage_state(path=str(state_path))
            try:
                state_path.chmod(0o600)
            except OSError:
                pass
            return {
                "status": "scheduled" if job.get("schedule_at") else "published",
                "published_url": current_url if "studio.bilibili.tv" not in current_url else "",
                "metadata": {**(job.get("metadata") or {}), "subtitle_uploaded": subtitle_uploaded, "submitted_at": utcnow(), "last_page_url": current_url},
            }
        except Exception:
            try:
                page.screenshot(path=str(screenshot_dir / "publish-error.png"), full_page=True)
            except Exception:
                pass
            raise
        finally:
            browser.close()


def publish_bilibili_job(job_id: str, *, headless: bool = HEADLESS) -> dict[str, Any]:
    job = get_publish_job(job_id)
    if job is None:
        raise ValueError("publish job not found")
    if job["platform"] != "bilibili_tv":
        raise ValueError("publish job is not a Bilibili job")
    if job["status"] != "approved":
        raise ValueError("publish job must be approved before publishing")
    _update_job(job_id, status="uploading", error="", metadata={**(job.get("metadata") or {}), "upload_started_at": utcnow()})
    try:
        result = _automate_publish(get_publish_job(job_id) or job, headless=headless)
        return _update_job(job_id, status=str(result["status"]), published_url=str(result.get("published_url", "")), error="", metadata=result.get("metadata", {}))
    except Exception as exc:
        failed = get_publish_job(job_id) or job
        metadata = dict(failed.get("metadata") or {})
        metadata["failed_at"] = utcnow()
        return _update_job(job_id, status="failed", error=str(exc), metadata=metadata)


def session_status(state_path: Path = STATE_PATH) -> dict[str, Any]:
    state_path = state_path.expanduser().resolve()
    return {"configured": state_path.is_file(), "state_path": str(state_path), "headless": HEADLESS, "studio_url": STUDIO_URL}


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="zMovie Bilibili Creator Center publisher")
    sub = parser.add_subparsers(dest="command", required=True)
    login = sub.add_parser("login", help="open a browser for one-time manual Google sign-in")
    login.add_argument("--state", default=str(STATE_PATH))
    prepare = sub.add_parser("prepare", help="prepare a Bilibili publish package")
    prepare.add_argument("--project", required=True)
    prepare.add_argument("--title", default="")
    prepare.add_argument("--description", default="")
    prepare.add_argument("--tags", default="")
    prepare.add_argument("--playlist", default="")
    prepare.add_argument("--type", dest="content_type", default="Original", choices=["Original", "Repost"])
    prepare.add_argument("--schedule-at", default="")
    prepare.add_argument("--subtitle", default="")
    approve = sub.add_parser("approve", help="approve a prepared publish job")
    approve.add_argument("--job", required=True)
    publish = sub.add_parser("publish", help="upload and submit an approved job")
    publish.add_argument("--job", required=True)
    publish.add_argument("--headed", action="store_true")
    status = sub.add_parser("status", help="show session or publish-job status")
    status.add_argument("--job", default="")
    args = parser.parse_args(argv)

    try:
        if args.command == "login":
            path = interactive_google_login(Path(args.state))
            _print({"status": "authenticated", "state_path": str(path)})
        elif args.command == "prepare":
            tags = [item.strip() for item in args.tags.split(",") if item.strip()] if args.tags else None
            _print(prepare_bilibili_publish(args.project, title=args.title, description=args.description, tags=tags, playlist=args.playlist, content_type=args.content_type, schedule_at=args.schedule_at, subtitle_path=args.subtitle))
        elif args.command == "approve":
            _print(approve_publish_job(args.job))
        elif args.command == "publish":
            _print(publish_bilibili_job(args.job, headless=not args.headed))
        elif args.command == "status":
            _print(get_publish_job(args.job) if args.job else session_status())
        return 0
    except Exception as exc:
        print(f"Bilibili publisher error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
