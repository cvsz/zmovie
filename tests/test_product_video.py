from __future__ import annotations

import unittest

from zmovie_platform.product_video import ProductProfile, assess_product


class ProductVideoTests(unittest.TestCase):
    def test_laptop_gets_high_suitability_and_technical_style(self) -> None:
        profile = ProductProfile.from_dict(
            {
                "name": "Example Laptop",
                "brand": "Example",
                "category": "gaming laptop electronics",
                "features": ["RTX-class GPU", "144Hz display", "16GB memory", "512GB SSD"],
                "benefits": ["smooth motion", "creator acceleration"],
                "regular_price": 34990,
                "sale_price": 31491,
            }
        )
        plan = assess_product(profile)
        self.assertEqual(plan.verdict, "high")
        self.assertEqual(plan.aspect_ratio, "9:16")
        self.assertEqual(plan.duration_seconds, 15)
        self.assertIn("technical product cinematography", plan.creative_style)
        self.assertIn("31491", plan.prompt.replace(",", ""))

    def test_generic_product_is_still_planable_without_price(self) -> None:
        profile = ProductProfile.from_dict(
            {
                "name": "Desk Organizer",
                "category": "office product",
                "features": ["three compartments"],
            }
        )
        plan = assess_product(profile)
        self.assertIn(plan.verdict, {"low", "medium", "high"})
        self.assertIn("Do not show a price", plan.prompt)

    def test_rejects_invalid_sale_price(self) -> None:
        with self.assertRaises(ValueError):
            ProductProfile.from_dict(
                {
                    "name": "Item",
                    "category": "electronics",
                    "regular_price": 100,
                    "sale_price": 120,
                }
            )

    def test_missing_identity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ProductProfile.from_dict({"name": "Only a name"})


if __name__ == "__main__":
    unittest.main()
