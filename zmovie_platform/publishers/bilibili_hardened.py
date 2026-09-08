from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from . import bilibili as legacy

_LOCK = threading.Lock()
_LEGACY_AUTOMATE = legacy._automate_publish
_BILIBILI_DOMAIN_SUFFIXES = ("bilibili.tv", "bilibili.com")

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


def _require_interactive_display() -> None:
    """Fail before Playwright launch when interactive login has no visible display."""
    if os.name != "posix":
        return
    if os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY"):
        return
    raise RuntimeError(
        "interactive Bilibili/Google login requires a visible GUI display; this host is headless. "
        "Run the login command on a GUI checkout, save storage_state.json there, then securely copy it "
        "to the server path configured by ZMOVIE_BILIBILI_STATE_PATH. xvfb-run alone is not sufficient "
        "because the operator must see and complete Google sign-in/2FA."
    )


def _default_chrome_user_data_dir() -> Path:
    """Return the platform default Chrome user-data directory used for live attach discovery."""
    if os.name == "nt":
        local_app_data = os.getenv("LOCALAPPDATA", "").strip()
        if not local_app_data:
            raise RuntimeError("LOCALAPPDATA is not set; pass --user-data-dir explicitly")
        return Path(local_app_data) / "Google" / "Chrome" / "User Data"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    return Path.home() / ".config" / "google-chrome"


def _devtools_ws_endpoint(user_data_dir: Path) -> str:
    """Read Chrome's live DevTools websocket endpoint from DevToolsActivePort."""
    port_file = user_data_dir.expanduser().resolve() / "DevToolsActivePort"
    if not port_file.is_file():
        raise RuntimeError(
            f"Chrome DevToolsActivePort was not found at {port_file}. Keep the Chrome session open, "
            "open chrome://inspect/#remote-debugging in that same Chrome, enable remote debugging, "
            "approve the connection prompt, then rerun this command. Do not expose a debugging port "
            "to the LAN."
        )
    lines = [line.strip() for line in port_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 2:
        raise RuntimeError(f"invalid Chrome DevToolsActivePort file: {port_file}")
    try:
        port = int(lines[0])
    except ValueError as exc:
        raise RuntimeError(f"invalid Chrome DevTools port in {port_file}: {lines[0]!r}") from exc
    if not (1 <= port <= 65535):
        raise RuntimeError(f"invalid Chrome DevTools port in {port_file}: {port}")
    websocket_path = lines[1]
    if not websocket_path.startswith("/"):
        raise RuntimeError(f"invalid Chrome DevTools websocket path in {port_file}")
    return f"ws://127.0.0.1:{port}{websocket_path}"


def _is_bilibili_host(value: str) -> bool:
    host = str(value or "").strip().lower().lstrip(".")
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in _BILIBILI_DOMAIN_SUFFIXES)


def _sanitize_storage_state(data: dict[str, Any]) -> dict[str, Any]:
    """Keep only Bilibili cookies and origin storage from a browser context snapshot."""
    cookies = [
        dict(cookie)
        for cookie in list(data.get("cookies") or [])
        if isinstance(cookie, dict) and _is_bilibili_host(str(cookie.get("domain") or ""))
    ]
    origins: list[dict[str, Any]] = []
    for origin in list(data.get("origins") or []):
        if not isinstance(origin, dict):
            continue
        parsed = urlparse(str(origin.get("origin") or ""))
        if parsed.hostname and _is_bilibili_host(parsed.hostname):
            origins.append(dict(origin))
    return {"cookies": cookies, "origins": origins}


def sanitize_storage_state_file(source: Path, output: Path) -> Path:
    """Write a least-privilege Bilibili-only Playwright storage-state file."""
    source = source.expanduser().resolve()
    output = output.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"browser state file not found: {source}")
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid browser state JSON: {source}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError("browser state must be a JSON object")
    scoped = _sanitize_storage_state(raw)
    if not scoped["cookies"] and not scoped["origins"]:
        raise RuntimeError("browser state contains no Bilibili cookies or origin storage")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(scoped, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        output.chmod(0o600)
    except OSError:
        pass
    return output


def capture_existing_chrome_session(
    state_path: Path,
    *,
    user_data_dir: Path | None = None,
    cdp_endpoint: str = "",
) -> Path:
    """Capture Bilibili auth state from an already-open Chrome profile via CDP.

    This does not launch a new browser and does not ask for Google credentials. The
    operator explicitly enables Chrome remote debugging locally, approves Chrome's
    connection prompt, and zMovie snapshots only Bilibili cookies/origin storage.
    """
    state_path = state_path.expanduser().resolve()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    endpoint = cdp_endpoint.strip()
    if not endpoint:
        endpoint = _devtools_ws_endpoint(user_data_dir or _default_chrome_user_data_dir())

    sync_playwright = legacy._playwright_import()
    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(endpoint, timeout=30000)
            contexts = list(browser.contexts)
            if not contexts:
                raise RuntimeError("connected Chrome has no browser context")
            context = contexts[0]

            page = next((item for item in context.pages if "studio.bilibili.tv" in item.url.lower()), None)
            created_page = False
            if page is None:
                page = context.new_page()
                created_page = True
                page.goto(legacy.STUDIO_URL, wait_until="domcontentloaded", timeout=legacy.TIMEOUT_MS)
            else:
                try:
                    page.reload(wait_until="domcontentloaded", timeout=legacy.TIMEOUT_MS)
                except Exception:
                    pass

            if not legacy._logged_in(page):
                if created_page:
                    try:
                        page.close()
                    except Exception:
                        pass
                raise RuntimeError(
                    "the attached Chrome profile is not authenticated in Bilibili Creator Center. "
                    "Sign in to https://studio.bilibili.tv/ in that same Chrome window, then rerun capture-chrome."
                )

            raw_state = context.storage_state(indexed_db=True)
            scoped_state = _sanitize_storage_state(raw_state)
            if not scoped_state["cookies"] and not scoped_state["origins"]:
                raise RuntimeError("authenticated Chrome context produced no Bilibili browser state")
            state_path.write_text(json.dumps(scoped_state, ensure_ascii=False, indent=2), encoding="utf-8")
            try:
                state_path.chmod(0o600)
            except OSError:
                pass
            if created_page:
                try:
                    page.close()
                except Exception:
                    pass
            browser.close()
            browser = None
    except Exception:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        raise

    return state_path


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

    capture = sub.add_parser("capture-chrome", help="capture Bilibili auth from an already-open Chrome session")
    capture.add_argument("--state", default=str(legacy.STATE_PATH))
    capture.add_argument("--user-data-dir", default="")
    capture.add_argument("--cdp-endpoint", default="")

    sanitize = sub.add_parser("sanitize-state", help="strip a browser state file down to Bilibili-only storage")
    sanitize.add_argument("--input", required=True)
    sanitize.add_argument("--output", required=True)

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
            _require_interactive_display()
            path = interactive_google_login(Path(args.state))
            _print({"status": "authenticated", "state_path": str(path)})
        elif args.command == "capture-chrome":
            data_dir = Path(args.user_data_dir) if args.user_data_dir else None
            path = capture_existing_chrome_session(
                Path(args.state),
                user_data_dir=data_dir,
                cdp_endpoint=args.cdp_endpoint,
            )
            scoped = json.loads(path.read_text(encoding="utf-8"))
            _print(
                {
                    "status": "captured",
                    "state_path": str(path),
                    "source": "existing_chrome",
                    "scope": "bilibili_only",
                    "cookies": len(scoped.get("cookies") or []),
                    "origins": len(scoped.get("origins") or []),
                }
            )
        elif args.command == "sanitize-state":
            path = sanitize_storage_state_file(Path(args.input), Path(args.output))
            scoped = json.loads(path.read_text(encoding="utf-8"))
            _print(
                {
                    "status": "sanitized",
                    "state_path": str(path),
                    "scope": "bilibili_only",
                    "cookies": len(scoped.get("cookies") or []),
                    "origins": len(scoped.get("origins") or []),
                }
            )
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
