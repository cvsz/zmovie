import unittest

from zmovie_platform.hyperframes import (
    TEMPLATE_CATEGORIES,
    apply_hyperframes_template,
    get_hyperframes_template,
    list_hyperframes_templates,
)


class HyperframesTemplateTests(unittest.TestCase):
    def test_ported_template_catalog_is_complete_and_safe(self):
        items = list_hyperframes_templates()
        self.assertEqual(len(items), 5)
        self.assertEqual(
            {item["category"] for item in items},
            set(TEMPLATE_CATEGORIES),
        )
        for item in items:
            self.assertTrue(item["preview_image"].startswith("/static/images/hyperframes/"))
            self.assertGreaterEqual(item["default_duration_seconds"], 3)
            self.assertGreaterEqual(len(item["safety_notes"]), 2)

    def test_filter_and_lookup(self):
        items = list_hyperframes_templates(category="comparison")
        self.assertEqual([item["id"] for item in items], ["compare-fair"])
        self.assertEqual(get_hyperframes_template("short-cut-social")["default_aspect_ratio"], "9:16")
        self.assertIsNone(get_hyperframes_template("missing-template"))

    def test_apply_template_adds_structure_and_safety_without_losing_brief(self):
        enhanced, template = apply_hyperframes_template("Launch zMovie", "showcase-clean")
        self.assertTrue(enhanced.startswith("Launch zMovie"))
        self.assertIn("Hyperframes template", enhanced)
        self.assertIn("Safety constraints", enhanced)
        self.assertEqual(template["id"], "showcase-clean")

    def test_unknown_template_fails_closed(self):
        with self.assertRaises(ValueError):
            apply_hyperframes_template("Launch zMovie", "does-not-exist")
        with self.assertRaises(ValueError):
            list_hyperframes_templates(category="unknown")


if __name__ == "__main__":
    unittest.main()
