from pathlib import Path

import pytest

from zmovie_platform.zflow import ZFlowI2VJob, product_ad_prompt


def test_product_ad_prompt_has_verified_specs_and_exact_discount() -> None:
    prompt = product_ad_prompt(1, price_mode="discount10")
    assert "RTX 4050 6GB" in prompt
    assert "144Hz" in prompt
    assert "31,491" in prompt
    assert "merchant authorizes" in prompt


def test_product_ad_prompt_full_price_does_not_claim_discount() -> None:
    prompt = product_ad_prompt(2, price_mode="full")
    assert "THB 34,990" in prompt
    assert "Do not claim a discount" in prompt


def test_product_ad_prompt_rejects_invalid_price_mode() -> None:
    with pytest.raises(ValueError):
        product_ad_prompt(price_mode="invalid")


def test_job_requires_existing_source_image(tmp_path: Path) -> None:
    job = ZFlowI2VJob(source_image=tmp_path / "missing.png", prompt="test")
    with pytest.raises(FileNotFoundError):
        job.validate()


def test_job_validates_supported_contract(tmp_path: Path) -> None:
    image = tmp_path / "product.png"
    image.write_bytes(b"fake-image-for-validation-only")
    job = ZFlowI2VJob(source_image=image, prompt="test", aspect_ratio="9:16", duration_seconds=5)
    job.validate()


def test_job_rejects_unsupported_duration(tmp_path: Path) -> None:
    image = tmp_path / "product.png"
    image.write_bytes(b"x")
    job = ZFlowI2VJob(source_image=image, prompt="test", duration_seconds=7)
    with pytest.raises(ValueError):
        job.validate()
