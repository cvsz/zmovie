from __future__ import annotations

import unittest
from unittest import mock

from zmovie_platform.publishers import bilibili as legacy
from zmovie_platform.publishers import bilibili_ui_compat as compat


class _Locator:
    def __init__(self, *, visible: bool = True, attrs: dict[str, str] | None = None) -> None:
        self._visible = visible
        self.attrs = attrs or {}
        self.filled = ""
        self.typed = ""

    @property
    def first(self):
        return self

    def count(self) -> int:
        return 1

    def is_visible(self) -> bool:
        return self._visible

    def get_attribute(self, name: str):
        return self.attrs.get(name)

    def fill(self, value: str) -> None:
        self.filled = value

    def click(self) -> None:
        return None

    def press(self, _key: str) -> None:
        return None

    def type(self, value: str, delay: int = 0) -> None:
        del delay
        self.typed = value

    def evaluate(self, _script: str):
        return "input"


class _Collection:
    def __init__(self, items: list[_Locator]) -> None:
        self.items = items

    def count(self) -> int:
        return len(self.items)

    def nth(self, index: int) -> _Locator:
        return self.items[index]


class _Page:
    def __init__(self, mapping: dict[str, _Locator] | None = None, controls: list[_Locator] | None = None) -> None:
        self.mapping = mapping or {}
        self.controls = controls or []
        self.frames = []
        self.main_frame = self
        self.url = "https://studio.bilibili.tv/upload"

    def locator(self, selector: str):
        if selector in self.mapping:
            return self.mapping[selector]
        if selector in {
            "input,textarea,[contenteditable='true'],[role='textbox']",
            "input:not([type='file']):not([type='hidden']),[contenteditable='true'],[role='textbox']",
            "textarea,[contenteditable='true']",
        }:
            return _Collection(self.controls)
        return _Collection([])

    def wait_for_timeout(self, _milliseconds: int) -> None:
        return None


class BilibiliUiCompatTests(unittest.TestCase):
    def test_title_uses_current_semantic_placeholder(self) -> None:
        field = _Locator(attrs={"placeholder": "Enter video title", "maxlength": "80", "type": "text"})
        page = _Page({"input[placeholder*='title' i]": field})
        compat._fill_required_compat(page, ["input[maxlength='100']"], "My title", "title")
        self.assertEqual(field.filled, "My title")

    def test_title_fallback_accepts_new_limit(self) -> None:
        field = _Locator(attrs={"placeholder": "Video name", "maxlength": "80", "type": "text"})
        page = _Page(controls=[field])
        found = compat._title_fallback(page)
        self.assertIs(found, field)

    def test_intro_fallback_prefers_description_control(self) -> None:
        field = _Locator(attrs={"placeholder": "Video description", "maxlength": "2000"})
        page = _Page(controls=[field])
        found = compat._intro_fallback(page)
        self.assertIs(found, field)

    def test_publish_restores_legacy_fill_hook(self) -> None:
        original = legacy._fill_required
        with mock.patch.object(compat.hardened, "publish_bilibili_job", return_value={"status": "submitted"}) as publish:
            result = compat.publish_bilibili_job("pub_example", headless=True)
        publish.assert_called_once_with("pub_example", headless=True)
        self.assertEqual(result["status"], "submitted")
        self.assertIs(legacy._fill_required, original)


if __name__ == "__main__":
    unittest.main()
