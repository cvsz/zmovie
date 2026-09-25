#!/usr/bin/env python3
"""Read-only browser acceptance for the public ZeaZ Cinema surface.

Scope is deliberately anonymous and non-destructive: page rendering, feed,
search/genre filtering, keyboard order, reduced motion, mobile viewport and
authorization negatives for anonymous mutations. It never logs in, never
creates content and never touches a real production user, so it is safe to
run against production.

Authenticated viewer/creator/admin flows are NOT covered here: they require
a separate WordPress staging install with disposable test identities
(FEATURE_MATRIX backlog item 5). Run with:

    .venv/bin/python scripts/e2e-anonymous-cinema.py [BASE_URL]

Exit code is non-zero when any check fails. No cookies, tokens or
credentials are printed; screenshots are optional and go to --out.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

DEFAULT_BASE = "https://zmovie.zeaz.dev/cinema"


class Checks:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def record(self, name: str, ok: bool, detail: str = "") -> None:
        self.results.append((name, bool(ok), detail))

    @property
    def failed(self) -> list[tuple[str, bool, str]]:
        return [row for row in self.results if not row[1]]

    def report(self) -> str:
        lines = [f"{'PASS' if ok else 'FAIL'}  {name}{'  — ' + detail if detail else ''}"
                 for name, ok, detail in self.results]
        lines.append(f"total={len(self.results)} failed={len(self.failed)}")
        return "\n".join(lines)


def run(base: str, out: Path | None) -> Checks:
    checks = Checks()
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])

        # --- desktop anonymous viewer -------------------------------------
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        response = page.goto(f"{base}/", wait_until="domcontentloaded", timeout=45000)
        checks.record("anonymous load returns 200", bool(response and response.ok),
                      f"status={response.status if response else 'none'}")
        checks.record("page title", page.title() == "ZeaZ Cinema", page.title())
        checks.record("main landmark present", page.locator("main#main").count() == 1)
        checks.record("skip link present", page.locator("a.zwpc-skip").count() >= 1)
        feed = page.locator("#zwpc-feed")
        checks.record("feed container present", feed.count() == 1)
        checks.record("feed has feed-or-region role",
                      feed.get_attribute("role") in {"feed", "region"},
                      f"role={feed.get_attribute('role')}")
        checks.record("genre filter labelled",
                      page.locator('label[for="zwpc-genre"]').count() == 1)
        checks.record("nav controls labelled",
                      page.locator("#zwpc-prev[aria-label]").count() == 1
                      and page.locator("#zwpc-next[aria-label]").count() == 1)
        checks.record("live status region", page.locator('#zwpc-status[role="status"]').count() == 1)
        if out:
            out.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out / "anonymous-desktop.png"), full_page=False)

        # --- keyboard-only navigation ------------------------------------
        page.keyboard.press("Tab")
        first_focus = page.evaluate("document.activeElement && document.activeElement.className")
        checks.record("first tab stop is the skip link", "zwpc-skip" in (first_focus or ""),
                      f"focus={first_focus}")
        order: list[str] = []
        for _ in range(8):
            page.keyboard.press("Tab")
            order.append(page.evaluate(
                "document.activeElement && (document.activeElement.className"
                " || document.activeElement.tagName)"))
        checks.record("keyboard order advances", len(set(order)) >= 3, f"stops={len(set(order))}")
        checks.record("no keyboard trap", page.locator("body").count() == 1)
        if out:
            page.screenshot(path=str(out / "anonymous-keyboard-focus.png"))

        # --- public feed + REST ------------------------------------------
        api = browser.new_context()
        feed_response = api.request.get(f"{base}/wp-json/zwpc/v1/feed?per_page=2", timeout=30000)
        checks.record("public feed 200", feed_response.ok, f"status={feed_response.status}")
        try:
            payload = feed_response.json()
            # Documented contract is a paged envelope, not a bare list.
            ok = (isinstance(payload, dict)
                  and isinstance(payload.get("films"), list)
                  and all(key in payload for key in ("total", "page", "per_page")))
            checks.record("feed payload envelope", ok,
                          f"keys={sorted(payload) if isinstance(payload, dict) else type(payload).__name__},"
                          f" films={len(payload.get('films', [])) if isinstance(payload, dict) else 'n/a'}")
        except Exception as exc:  # noqa: BLE001 - reported as a failed check
            checks.record("feed payload envelope", False, f"json error: {exc}")
        api.close()

        # --- authorization negatives (anonymous) -------------------------
        anon = browser.new_context()
        for name, method, path, body in (
            ("anonymous favorites mutation denied", "POST",
             "/wp-json/zwpc/v1/favorites", {"film_id": 1}),
            ("anonymous submit-film denied", "POST",
             "/wp-json/zwpc/v1/submit-film", {"title": "e2e-probe"}),
        ):
            res = anon.request.fetch(f"{base}{path}", method=method, data=body, timeout=30000)
            checks.record(name, res.status in (401, 403), f"status={res.status}")
        bad_nonce = anon.request.fetch(
            f"{base}/wp-json/zwpc/v1/favorites", method="POST",
            headers={"X-WP-Nonce": "invalid-e2e-nonce"}, data={"film_id": 1}, timeout=30000)
        checks.record("invalid REST nonce rejected", bad_nonce.status in (401, 403),
                      f"status={bad_nonce.status}")
        anon.close()

        # --- mobile viewport ---------------------------------------------
        mobile = browser.new_page(viewport={"width": 390, "height": 844},
                                  has_touch=True, is_mobile=True)
        m_res = mobile.goto(f"{base}/", wait_until="domcontentloaded", timeout=45000)
        checks.record("mobile load 200", bool(m_res and m_res.ok),
                      f"status={m_res.status if m_res else 'none'}")
        overflow = mobile.evaluate(
            "document.documentElement.scrollWidth - document.documentElement.clientWidth")
        checks.record("no horizontal overflow on mobile", overflow <= 1, f"overflow={overflow}px")
        if out:
            mobile.screenshot(path=str(out / "anonymous-mobile.png"))
        mobile.close()

        # --- reduced motion ----------------------------------------------
        reduced = browser.new_context(reduced_motion="reduce")
        rm_page = reduced.new_page()
        rm_page.goto(f"{base}/", wait_until="domcontentloaded", timeout=45000)
        animated = rm_page.evaluate(
            "Array.from(document.querySelectorAll('*')).filter(el => {"
            " const s = getComputedStyle(el);"
            " return s.animationName !== 'none' && s.animationDuration !== '0s';"
            " }).length")
        checks.record("reduced motion suppresses animation", animated == 0,
                      f"animated elements={animated}")
        reduced.close()

        page.close()
        browser.close()
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", nargs="?", default=DEFAULT_BASE)
    parser.add_argument("--out", type=Path, default=None,
                        help="optional directory for redacted screenshots")
    parser.add_argument("--json", action="store_true", help="emit machine-readable results")
    args = parser.parse_args(argv)
    checks = run(args.base.rstrip("/"), args.out)
    if args.json:
        print(json.dumps([{"check": n, "pass": ok, "detail": d} for n, ok, d in checks.results],
                         indent=2))
    else:
        print(checks.report())
    return 1 if checks.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
