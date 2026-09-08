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
    """Return the first matching file input even when it is hidden.

    Playwright set_input_files() works on hidden file inputs, which is common in
    upload UIs. Requiring visibility here makes otherwise valid upload controls
    look missing.
    """
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

    # A successful form submission is not proof that the video is publicly
    # visible or accepted by downstream moderation. Keep that distinction in
    # the durable job state until a remote confirmation step exists.
    return {**result, "status": "submitted", "published_url": "", "metadata": metadata}


def publish_bilibili_job(job_id: str, *, headless: bool = legacy.HEADLESS) -> dict[str, Any]:
    """Publish through the legacy automation with hardened upload/session semantics."""
    with _LOCK:
        old_automate = legacy._automate_publish
        legacy._automate_publish = _automate_publish
        try:
            return legacy.publish_bilibili_job(job_id, headless=headless)
        finally:
            legacy._automate_publish = old_automate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hardened zMovie Bilibili operations")
    sub = parser.add_subparsers(dest="command", required=True)
    login = sub.add_parser("login", help="open interactive browser for one-time Google sign-in")
    login.add_argument("--state", default=str(legacy.STATE_PATH))
    status = sub.add_parser("session", help="validate the saved Creator Center session")
    status.add_argument("--state", default=str(legacy.STATE_PATH))
    status.add_argument("--no-probe", action="store_true")
    publish = sub.add_parser("publish", help="upload and submit an approved job")
    publish.add_argument("--job", required=True)
    publish.add_argument("--headed", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.command == "login":
            path = interactive_google_login(Path(args.state))
            print(json.dumps({"status": "authenticated", "state_path": str(path)}, ensure_ascii=False, indent=2))
        elif args.command == "session":
            print(json.dumps(session_status(Path(args.state), probe=not args.no_probe), ensure_ascii=False, indent=2))
        elif args.command == "publish":
            print(json.dumps(publish_bilibili_job(args.job, headless=not args.headed), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"Bilibili hardened publisher error: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
