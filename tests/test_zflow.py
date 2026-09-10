from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from zmovie_platform.zflow import ZFlowI2VJob, product_ad_prompt


class ZFlowTests(unittest.TestCase):
    def test_product_ad_prompt_has_verified_specs_and_exact_discount(self) -> None:
        prompt = product_ad_prompt(1, price_mode="discount10")
        self.assertIn("RTX 4050 6GB", prompt)
        self.assertIn("144Hz", prompt)
        self.assertIn("31,491", prompt)
        self.assertIn("merchant authorizes", prompt)

    def test_product_ad_prompt_full_price_does_not_claim_discount(self) -> None:
        prompt = product_ad_prompt(2, price_mode="full")
        self.assertIn("THB 34,990", prompt)
        self.assertIn("Do not claim a discount", prompt)

    def test_product_ad_prompt_rejects_invalid_price_mode(self) -> None:
        with self.assertRaises(ValueError):
            product_ad_prompt(price_mode="invalid")

    def test_job_requires_existing_source_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job = ZFlowI2VJob(source_image=Path(tmp) / "missing.png", prompt="test")
            with self.assertRaises(FileNotFoundError):
                job.validate()

    def test_job_validates_supported_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "product.png"
            image.write_bytes(b"fake-image-for-validation-only")
            job = ZFlowI2VJob(source_image=image, prompt="test", aspect_ratio="9:16", duration_seconds=5)
            job.validate()

    def test_job_rejects_unsupported_duration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "product.png"
            image.write_bytes(b"x")
            job = ZFlowI2VJob(source_image=image, prompt="test", duration_seconds=7)
            with self.assertRaises(ValueError):
                job.validate()


if __name__ == "__main__":
    unittest.main()
