from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from . import bilibili as legacy

_NOT_PUBLIC_MARKERS = (
    "page not found",
    "video not found",
    "video unavailable",
    "this video is unavailable",
    "404",
)


def _is_public_bilibili_video_url(value: str) -> bool:
    try:
        parsed = urlparse(str(value or "").strip())
    except ValueError:
        return False
    host = (parsed.hostname or "").lower().lstrip(".")
    if parsed.scheme != "https":
        return False
    if not (host == "bilibili.tv" or host.endswith(".bilibili.tv")):
        return False
    return "/video/" in parsed.path.lower()


def _probe_public_url(url: str, *, state_path: Path = legacy.STATE_PATH) -> dict[str, Any]:
    state_path = state_path.expanduser().resolve()
    if not state_path.is_file():
        raise RuntimeError(f"Bilibili browser session not found at {state_path}")

    sync_playwright = legacy._playwright_import()
    browser = None
    try:
        with sync_playwright() as p:
            browser, context = legacy._browser_context(p, headless=True, state_path=state_path)
            page = context.new_page()
            response = page.goto(url, wait_until="domcontentloaded", timeout=legacy.TIMEOUT_MS)
            final_url = str(page.url or "")
            if not _is_public_bilibili_video_url(final_url):
                raise RuntimeError(f"public URL probe redirected outside a Bilibili video page: {final_url}")

            status = getattr(response, "status", None) if response is not None else None
            if isinstance(status, int) and status >= 400:
                raise RuntimeError(f"public URL probe returned HTTP {status}")

            body = ""
            try:
                body = page.locator("body").inner_text(timeout=5000)
            except Exception:
                pass
            lower = body.lower()
            if any(marker in lower for marker in _NOT_PUBLIC_MARKERS):
                raise RuntimeError("public URL probe indicates the video is not publicly available")

            result = {
                "reachable": True,
                "requested_url": url,
                "final_url": final_url,
                "http_status": status,
            }
            browser.close()
            browser = None
            return result
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass


def confirm_publication(
    job_id: str,
    url: str,
    *,
    state_path: Path = legacy.STATE_PATH,
    probe: bool = True,
) -> dict[str, Any]:
    """Promote a submitted Bilibili job to published only after public-URL confirmation."""
    job = legacy.get_publish_job(job_id)
    if job is None:
        raise ValueError("publish job not found")
    if job.get("platform") != "bilibili_tv":
        raise ValueError("publish job is not a Bilibili job")
    if job.get("status") not in {"submitted", "published"}:
        raise ValueError(f"public confirmation requires submitted/published status, got {job.get('status')}")

    candidate = str(url or "").strip()
    if not _is_public_bilibili_video_url(candidate):
        raise ValueError("confirmation URL must be an HTTPS bilibili.tv /video/ URL")

    if job.get("status") == "published" and job.get("published_url") == candidate:
        metadata = dict(job.get("metadata") or {})
        if metadata.get("remote_confirmation"):
            return job

    probe_result: dict[str, Any] = {
        "reachable": False,
        "requested_url": candidate,
        "final_url": candidate,
        "http_status": None,
    }
    if probe:
        probe_result = _probe_public_url(candidate, state_path=state_path)
        candidate = str(probe_result["final_url"])

    metadata = dict(job.get("metadata") or {})
    metadata.update(
        {
            "remote_confirmation": True,
            "remote_confirmed_at": legacy.utcnow(),
            "remote_confirmation_source": "public_url_probe" if probe else "operator_url_no_probe",
            "remote_confirmation_probe": probe_result,
        }
    )
    return legacy._update_job(
        job_id,
        status="published",
        published_url=candidate,
        error="",
        metadata=metadata,
    )


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Confirm a submitted zMovie Bilibili publication")
    parser.add_argument("--job", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--state", default=str(legacy.STATE_PATH))
    parser.add_argument(
        "--no-probe",
        action="store_true",
        help="record an operator-provided URL without a live probe (not recommended for production evidence)",
    )
    args = parser.parse_args(argv)
    try:
        _print(
            confirm_publication(
                args.job,
                args.url,
                state_path=Path(args.state),
                probe=not args.no_probe,
            )
        )
        return 0
    except Exception as exc:
        print(f"Bilibili confirmation error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
