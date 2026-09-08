from __future__ import annotations

import argparse
import json
import threading
from pathlib import Path
from typing import Any

from . import bilibili as legacy

_LOCK = threading.Lock()
_LEGACY_AUTOMATE = legacy._automate_publish

prepare_bilibili_publish = legacy.prepare_bilibili_publish
approve_publish_job = legacy.approve_publish_job
get_publish_job = legacy.get_publish_job
list_publish_jobs = legacy.list_publish_jobs
interactive_google_login = legacy.interactive_google_login


def _file_input(page: Any, selectors: list[str]) -> Any | None:
    """Return the first matching file input even when it is hidden."""
    for selector in selectors:
        try:
            locator = page.locator(selector)
            if locator.count() > 0:
                return locator.first
        except Exception:
            continue
    return None


def _set_video(page: Any, path: str) -> None:
    locator = _file_input(
        page,
        [
            "input[type=file][accept*='video']",
            "input[type=file][accept*='.mp4']",
            "input[type=file]",
        ],
    )
    if locator is None:
        raise RuntimeError("could not locate Creator Center video file input")
    locator.set_input_files(path)


def session_status(state_path: Path = legacy.STATE_PATH, *, probe: bool = True) -> dict[str, Any]:
    """Report whether the saved browser session exists and is actually usable."""
    state_path = state_path.expanduser().resolve()
    result: dict[str, Any] = {
        "configured": state_path.is_file(),
        "authenticated": False,
        "checked": False,
        "state_path": str(state_path),
        "headless": legacy.HEADLESS,
        "studio_url": legacy.STUDIO_URL,
    }
    if not result["configured"] or not probe:
        return result

    browser = None
    try:
        sync_playwright = legacy._playwright_import()
        with sync_playwright() as p:
            browser, context = legacy._browser_context(p, headless=True, state_path=state_path)
            page = context.new_page()
            page.goto(legacy.STUDIO_URL, wait_until="domcontentloaded", timeout=legacy.TIMEOUT_MS)
            result["checked"] = True
            result["authenticated"] = bool(legacy._logged_in(page))
            result["last_page_url"] = page.url
            if not result["authenticated"]:
                result["error"] = "session_expired_or_not_authenticated"
            browser.close()
            browser = None
    except Exception as exc:
        result["checked"] = True
        result["error"] = str(exc)[:500]
        result["authenticated"] = False
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
    return result


def _automate_publish(job: dict[str, Any], *, headless: bool = legacy.HEADLESS, state_path: Path = legacy.STATE_PATH) -> dict[str, Any]:
    old_set_video = legacy._set_video
    legacy._set_video = _set_video
    try:
        result = _LEGACY_AUTOMATE(job, headless=headless, state_path=state_path)
    finally:
        legacy._set_video = old_set_video

    metadata = dict(result.get("metadata") or {})
    metadata["release_mode"] = "scheduled" if job.get("schedule_at") else "immediate"
    metadata["remote_confirmation"] = False

    candidate_url = str(result.get("published_url") or "")
    confirmed_public = bool(candidate_url and "bilibili.tv/video/" in candidate_url.lower())
    if confirmed_public:
        metadata["remote_confirmation"] = True
        return {**result, "status": "published", "metadata": metadata}

    # A successful form submit is not proof that Creator Center accepted the
    # item through moderation or that it is publicly visible.
    return {**result, "status": "submitted", "published_url": "", "metadata": metadata}


def publish_bilibili_job(job_id: str, *, headless: bool = legacy.HEADLESS) -> dict[str, Any]:
    """Publish through the existing automation with hardened upload semantics."""
    with _LOCK:
        old_automate = legacy._automate_publish
        legacy._automate_publish = _automate_publish
        try:
            return legacy.publish_bilibili_job(job_id, headless=headless)
        finally:
            legacy._automate_publish = old_automate


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hardened zMovie Bilibili operations")
    sub = parser.add_subparsers(dest="command", required=True)

    login = sub.add_parser("login", help="open interactive browser for one-time Google sign-in")
    login.add_argument("--state", default=str(legacy.STATE_PATH))

    session = sub.add_parser("session", help="validate the saved Creator Center session")
    session.add_argument("--state", default=str(legacy.STATE_PATH))
    session.add_argument("--no-probe", action="store_true")

    prepare = sub.add_parser("prepare", help="prepare Bilibili metadata, cover and publication manifest")
    prepare.add_argument("--project", required=True)
    prepare.add_argument("--title", default="")
    prepare.add_argument("--description", default="")
    prepare.add_argument("--tags", default="")
    prepare.add_argument("--playlist", default="")
    prepare.add_argument("--type", dest="content_type", default="Original", choices=["Original", "Repost"])
    prepare.add_argument("--schedule-at", default="")
    prepare.add_argument("--subtitle", default="")

    approve = sub.add_parser("approve", help="approve a prepared publication job")
    approve.add_argument("--job", required=True)

    publish = sub.add_parser("publish", help="upload and submit an approved job")
    publish.add_argument("--job", required=True)
    publish.add_argument("--headed", action="store_true")

    status = sub.add_parser("status", help="show one publish job")
    status.add_argument("--job", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "login":
            path = interactive_google_login(Path(args.state))
            _print({"status": "authenticated", "state_path": str(path)})
        elif args.command == "session":
            _print(session_status(Path(args.state), probe=not args.no_probe))
        elif args.command == "prepare":
            tags = [item.strip() for item in args.tags.split(",") if item.strip()] if args.tags else None
            _print(
                prepare_bilibili_publish(
                    args.project,
                    title=args.title,
                    description=args.description,
                    tags=tags,
                    playlist=args.playlist,
                    content_type=args.content_type,
                    schedule_at=args.schedule_at,
                    subtitle_path=args.subtitle,
                )
            )
        elif args.command == "approve":
            _print(approve_publish_job(args.job))
        elif args.command == "publish":
            _print(publish_bilibili_job(args.job, headless=not args.headed))
        elif args.command == "status":
            job = get_publish_job(args.job)
            if job is None:
                raise ValueError("publish job not found")
            _print(job)
        return 0
    except Exception as exc:
        print(f"Bilibili hardened publisher error: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
