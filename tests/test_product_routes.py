from __future__ import annotations

import unittest

from fastapi import HTTPException

from zmovie_platform.product_routes import plan_product_video


class ProductRouteTests(unittest.TestCase):
    def test_plan_returns_serializable_product_and_plan(self) -> None:
        payload = {
            "name": "Mechanical Keyboard",
            "category": "electronics accessory",
            "features": ["Bluetooth", "Hot-swappable switches"],
            "benefits": ["Portable"],
            "regular_price": 2490,
            "sale_price": 2190,
            "currency": "THB",
        }

        result = plan_product_video(payload)

        self.assertEqual(result["product"]["name"], "Mechanical Keyboard")
        self.assertGreaterEqual(result["plan"]["score"], 60)
        self.assertEqual(result["plan"]["aspect_ratio"], "9:16")
        self.assertIn("Mechanical Keyboard", result["plan"]["prompt"])

    def test_plan_rejects_invalid_product(self) -> None:
        with self.assertRaises(HTTPException) as context:
            plan_product_video({"name": "Missing category"})
        self.assertEqual(context.exception.status_code, 422)

    def test_plan_rejects_invalid_feature_type(self) -> None:
        with self.assertRaises(HTTPException) as context:
            plan_product_video({"name": "Bad", "category": "generic", "features": 123})
        self.assertEqual(context.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
