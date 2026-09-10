from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException

from .product_video import ProductProfile, assess_product

router = APIRouter(prefix="/api/v2/products", tags=["product-video"])


@router.post("/plan")
def plan_product_video(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a reusable product profile and return its deterministic video plan."""
    try:
        profile = ProductProfile.from_dict(payload)
        plan = assess_product(profile)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "product": asdict(profile),
        "plan": asdict(plan),
    }
