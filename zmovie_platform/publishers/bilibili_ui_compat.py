from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any

from . import bilibili as legacy
from . import bilibili_hardened as hardened

FIELD_WAIT_MS = max(5000, min(int(os.getenv("ZMOVIE_BILIBILI_FIELD_WAIT_MS", "60000")), 180000))

_TITLE_SELECTORS = [
    "input[placeholder*='title' i]",
    "input[name*='title' i]",
    "input[id*='title' i]",
    "input[aria-label*='title' i]",
    "textarea[placeholder*='title' i]",
    "[contenteditable='true'][data-placeholder*='title' i]",
    "[contenteditable='true'][aria-label*='title' i]",
    "[role='textbox'][data-placeholder*='title' i]",
    "input[maxlength='100']",
    "input[maxlength='80']",
]

_INTRO_SELECTORS = [
    "textarea[placeholder*='introduction' i]",
    "textarea[placeholder*='description' i]",
    "textarea[placeholder*='desc' i]",
    "textarea[name*='description' i]",
    "textarea[id*='description' i]",
    "textarea[maxlength='2000']",
    "[contenteditable='true'][data-placeholder*='introduction' i]",
    "[contenteditable='true'][data-placeholder*='description' i]",
    "[contenteditable='true'][aria-label*='description' i]",
    "textarea",
]


def _roots(page: Any) -> list[Any]:
    roots: list[Any] = [page]
    try:
        main = page.main_frame
        for frame in list(page.frames):
            if frame is not main:
                roots.append(frame)
    except Exception:
        pass
    return roots


def _visible(locator: Any) -> bool:
    try:
        return locator.count() > 0 and locator.first.is_visible()
    except Exception:
        return False


def _find(page: Any, selectors: list[str]) -> Any | None:
    for root in _roots(page):
        for selector in selectors:
            try:
                locator = root.locator(selector)
                if _visible(locator):
                    return locator.first
            except Exception:
                continue
    return None


def _attr(locator: Any, name: str) -> str:
    try:
        return str(locator.get_attribute(name) or "")
    except Exception:
        return ""


def _safe_control_diagnostics(page: Any, limit: int = 40) -> list[dict[str, str]]:
    """Describe form controls without capturing values, cookies, or storage state."""
    output: list[dict[str, str]] = []
    for root in _roots(page):
        frame_url = str(getattr(root, "url", "") or getattr(page, "url", ""))
        try:
            controls = root.locator("input,textarea,[contenteditable='true'],[role='textbox']")
            count = min(int(controls.count()), limit - len(output))
        except Exception:
            continue
        for index in range(max(count, 0)):
            locator = controls.nth(index)
            try:
                if not locator.is_visible():
                    continue
            except Exception:
                continue
            try:
                tag = str(locator.evaluate("el => el.tagName.toLowerCase()"))
            except Exception:
                tag = ""
            output.append(
                {
                    "frame": frame_url[:240],
                    "tag": tag,
                    "type": _attr(locator, "type")[:80],
                    "name": _attr(locator, "name")[:120],
                    "id": _attr(locator, "id")[:120],
                    "placeholder": _attr(locator, "placeholder")[:200],
                    "aria_label": _attr(locator, "aria-label")[:200],
                    "maxlength": _attr(locator, "maxlength")[:32],
                    "contenteditable": _attr(locator, "contenteditable")[:32],
                }
            )
            if len(output) >= limit:
                return output
    return output


def _title_fallback(page: Any) -> Any | None:
    best: tuple[int, Any] | None = None
    for root in _roots(page):
        try:
            controls = root.locator("input:not([type='file']):not([type='hidden']),[contenteditable='true'],[role='textbox']")
            count = min(int(controls.count()), 80)
        except Exception:
            continue
        for index in range(count):
            locator = controls.nth(index)
            try:
                if not locator.is_visible():
                    continue
            except Exception:
                continue
            text = " ".join(
                [
                    _attr(locator, "name"),
                    _attr(locator, "id"),
                    _attr(locator, "placeholder"),
                    _attr(locator, "aria-label"),
                    _attr(locator, "data-placeholder"),
                ]
            ).lower()
            if any(token in text for token in ("tag", "search", "date", "time", "playlist")):
                continue
            score = 0
            if "title" in text:
                score += 20
            maximum = _attr(locator, "maxlength")
            try:
                max_value = int(maximum)
            except ValueError:
                max_value = 0
            if 40 <= max_value <= 200:
                score += 6
            if _attr(locator, "type").lower() in {"", "text"}:
                score += 2
            if best is None or score > best[0]:
                best = (score, locator)
    return best[1] if best is not None and best[0] >= 6 else None


def _intro_fallback(page: Any) -> Any | None:
    for root in _roots(page):
        try:
            controls = root.locator("textarea,[contenteditable='true']")
            count = min(int(controls.count()), 80)
        except Exception:
            continue
        candidates: list[tuple[int, Any]] = []
        for index in range(count):
            locator = controls.nth(index)
            try:
                if not locator.is_visible():
                    continue
            except Exception:
                continue
            text = " ".join(
                [
                    _attr(locator, "name"),
                    _attr(locator, "id"),
                    _attr(locator, "placeholder"),
                    _attr(locator, "aria-label"),
                    _attr(locator, "data-placeholder"),
                ]
            ).lower()
            score = 1
            if any(token in text for token in ("description", "introduction", "intro", "desc")):
                score += 20
            maximum = _attr(locator, "maxlength")
            try:
                if int(maximum) >= 500:
                    score += 5
            except ValueError:
                pass
            candidates.append((score, locator))
        if candidates:
            candidates.sort(key=lambda item: item[0], reverse=True)
            return candidates[0][1]
    return None


def _locate_required(page: Any, selectors: list[str], label: str) -> Any:
    label_key = label.strip().lower()
    expanded = list(selectors)
    if label_key == "title":
        expanded = _TITLE_SELECTORS + expanded
    elif label_key in {"introduction", "description"}:
        expanded = _INTRO_SELECTORS + expanded

    deadline = time.monotonic() + (FIELD_WAIT_MS / 1000.0)
    while True:
        locator = _find(page, expanded)
        if locator is None and label_key == "title":
            locator = _title_fallback(page)
        elif locator is None and label_key in {"introduction", "description"}:
            locator = _intro_fallback(page)
        if locator is not None:
            return locator

        if time.monotonic() >= deadline:
            diagnostics = _safe_control_diagnostics(page)
            diagnostic_text = json.dumps(diagnostics, ensure_ascii=False, separators=(",", ":"))
            raise RuntimeError(
                f"could not locate Bilibili {label} field after {FIELD_WAIT_MS // 1000}s; "
                f"url={getattr(page, 'url', '')}; visible_controls={diagnostic_text[:6000]}"
            )
        try:
            page.wait_for_timeout(500)
        except Exception:
            time.sleep(0.5)


def _fill_required_compat(page: Any, selectors: list[str], value: str, label: str) -> None:
    locator = _locate_required(page, selectors, label)
    try:
        locator.fill(value)
        return
    except Exception:
        pass
    try:
        locator.click()
        locator.press("Control+A")
        locator.type(value, delay=5)
        return
    except Exception as exc:
        raise RuntimeError(f"located Bilibili {label} field but could not fill it: {exc}") from exc


def publish_bilibili_job(job_id: str, *, headless: bool = legacy.HEADLESS) -> dict[str, Any]:
    """Retry hardened publication with UI-compatible delayed metadata-field discovery."""
    old_fill = legacy._fill_required
    legacy._fill_required = _fill_required_compat
    try:
        return hardened.publish_bilibili_job(job_id, headless=headless)
    finally:
        legacy._fill_required = old_fill


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bilibili Creator Center UI compatibility publisher")
    sub = parser.add_subparsers(dest="command", required=True)
    publish = sub.add_parser("publish", help="publish an approved job with delayed-field compatibility")
    publish.add_argument("--job", required=True)
    publish.add_argument("--headed", action="store_true")
    status = sub.add_parser("status", help="show one publish job")
    status.add_argument("--job", required=True)
    args = parser.parse_args(argv)

    try:
        if args.command == "publish":
            _print(publish_bilibili_job(args.job, headless=not args.headed))
        else:
            job = hardened.get_publish_job(args.job)
            if job is None:
                raise ValueError("publish job not found")
            _print(job)
        return 0
    except Exception as exc:
        print(f"Bilibili UI compatibility publisher error: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
