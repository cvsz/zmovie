#!/usr/bin/env python3
"""ตรวจ syntax ของ JavaScript ที่ฝังอยู่ในหน้า Studio ด้วย Node.js."""

from __future__ import annotations

import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path


class InlineScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.current: list[str] | None = None
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script" and not dict(attrs).get("src"):
            self.current = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.current is not None:
            self.scripts.append("".join(self.current))
            self.current = None

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.current.append(data)


def main() -> int:
    html_path = Path(__file__).resolve().parents[1] / "static" / "studio.html"
    parser = InlineScriptParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    if not parser.scripts:
        print(f"No inline scripts found in {html_path}", file=sys.stderr)
        return 1

    node_bin = shutil.which("node") or "node"
    for index, script in enumerate(parser.scripts, start=1):
        result = subprocess.run(
            [node_bin, "--check", "-"],
            input=script,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            print(f"Inline script {index} in {html_path} has invalid JavaScript:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return result.returncode
    print(f"Inline JavaScript syntax passed: {len(parser.scripts)} script(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
