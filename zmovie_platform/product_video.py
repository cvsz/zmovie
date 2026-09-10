from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProductProfile:
    name: str
    category: str
    brand: str = ""
    description: str = ""
    features: tuple[str, ...] = ()
    benefits: tuple[str, ...] = ()
    regular_price: float | None = None
    sale_price: float | None = None
    currency: str = "THB"
    audience: str = "general consumers"
    cta: str = "สั่งซื้อเลย"
    visual_notes: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ProductProfile:
        name = str(payload.get("name", "")).strip()
        category = str(payload.get("category", "")).strip()
        if not name or not category:
            raise ValueError("product requires non-empty name and category")

        def items(key: str) -> tuple[str, ...]:
            value = payload.get(key, [])
            if isinstance(value, str):
                return (value.strip(),) if value.strip() else ()
            if not isinstance(value, list):
                raise TypeError(f"{key} must be a string or list")
            return tuple(str(item).strip() for item in value if str(item).strip())

        def price(key: str) -> float | None:
            value = payload.get(key)
            if value in (None, ""):
                return None
            number = float(value)
            if number < 0:
                raise ValueError(f"{key} must not be negative")
            return number

        regular = price("regular_price")
        sale = price("sale_price")
        if regular is not None and sale is not None and sale > regular:
            raise ValueError("sale_price must not exceed regular_price")

        return cls(
            name=name,
            category=category,
            brand=str(payload.get("brand", "")).strip(),
            description=str(payload.get("description", "")).strip(),
            features=items("features"),
            benefits=items("benefits"),
            regular_price=regular,
            sale_price=sale,
            currency=str(payload.get("currency", "THB")).strip() or "THB",
            audience=str(payload.get("audience", "general consumers")).strip() or "general consumers",
            cta=str(payload.get("cta", "สั่งซื้อเลย")).strip() or "สั่งซื้อเลย",
            visual_notes=str(payload.get("visual_notes", "")).strip(),
        )


@dataclass(frozen=True)
class ProductVideoPlan:
    score: int
    verdict: str
    reasons: tuple[str, ...]
    aspect_ratio: str
    duration_seconds: int
    creative_style: str
    pacing: str
    emphasis: tuple[str, ...]
    prompt: str
    negative_prompt: str


def assess_product(profile: ProductProfile) -> ProductVideoPlan:
    """Score a product and derive a conservative, reusable video treatment.

    This is intentionally deterministic and claim-safe. It only uses facts supplied
    in the product profile and never invents specifications, savings, scarcity, or
    performance claims.
    """

    category = profile.category.lower()
    score = 45
    reasons: list[str] = []

    if profile.features:
        score += min(20, len(profile.features) * 4)
        reasons.append("มี feature ที่นำมาทำ visual proof/spec cards ได้")
    else:
        reasons.append("ข้อมูล feature ยังน้อย ควรเพิ่มรายละเอียดก่อน render")

    if profile.benefits:
        score += min(15, len(profile.benefits) * 5)
        reasons.append("มี benefit สำหรับเปลี่ยนจากข้อมูลสินค้าเป็นเหตุผลในการซื้อ")

    if profile.regular_price is not None or profile.sale_price is not None:
        score += 10
        reasons.append("มีราคาเพียงพอสำหรับ price reveal ที่ตรวจสอบได้")

    visual_categories = (
        "electronics",
        "computer",
        "laptop",
        "phone",
        "fashion",
        "beauty",
        "food",
        "home",
        "furniture",
        "appliance",
        "automotive",
        "toy",
        "accessory",
    )
    if any(token in category for token in visual_categories):
        score += 10
        reasons.append("หมวดสินค้านี้เหมาะกับ short-form visual demonstration")

    score = max(0, min(100, score))
    verdict = "high" if score >= 80 else "medium" if score >= 60 else "low"

    if any(token in category for token in ("laptop", "computer", "electronics", "phone", "gaming")):
        style = "premium technical product cinematography with crisp macro details and restrained motion graphics"
        pacing = "energetic but readable"
        emphasis = ("hero product", "top specifications", "real-world benefits", "price", "CTA")
        duration = 15
    elif any(token in category for token in ("fashion", "beauty", "cosmetic", "accessory")):
        style = "aspirational lifestyle product cinematography with texture, material and close-up detail"
        pacing = "smooth and stylish"
        emphasis = ("appearance", "material/detail", "benefits", "price", "CTA")
        duration = 12
    elif any(token in category for token in ("food", "drink", "beverage")):
        style = "appetizing sensory commercial cinematography with macro texture and serving moments"
        pacing = "fast sensory cuts"
        emphasis = ("hero serving", "texture", "benefits", "price", "CTA")
        duration = 10
    else:
        style = "clean premium ecommerce product cinematography faithful to the source image"
        pacing = "clear and conversion-focused"
        emphasis = ("hero product", "key features", "benefits", "price", "CTA")
        duration = 12

    facts = [*profile.features, *profile.benefits]
    fact_text = "; ".join(facts) if facts else "Use only visible product details from the source image and supplied description."

    price_parts: list[str] = []
    if profile.regular_price is not None:
        price_parts.append(f"regular price {profile.currency} {profile.regular_price:,.2f}")
    if profile.sale_price is not None:
        price_parts.append(f"sale price {profile.currency} {profile.sale_price:,.2f}")
    price_text = ", ".join(price_parts) if price_parts else "Do not show a price unless supplied by the operator."

    brand_name = f"{profile.brand} {profile.name}".strip()
    description = profile.description or "No additional description supplied."
    visual_notes = profile.visual_notes or "Preserve the exact product identity, geometry, materials, labels and proportions from the source image."

    prompt = (
        f"Create a vertical 9:16 ecommerce video for {brand_name}. Category: {profile.category}. "
        f"Target audience: {profile.audience}. Creative direction: {style}; pacing: {pacing}. "
        f"Product description: {description} Facts allowed on screen: {fact_text} Pricing: {price_text}. "
        f"Visual guidance: {visual_notes} Build a concise sequence around {', '.join(emphasis)}. "
        f"End with CTA: {profile.cta}. Use readable typography inside mobile safe margins. "
        "Never invent specifications, certifications, benchmarks, medical claims, savings, discounts, gifts, stock scarcity, reviews or guarantees. "
        "If a supplied fact cannot be visually demonstrated, present it only as restrained text rather than fabricating evidence."
    )

    negative = (
        "wrong product, altered logo, fake labels, warped geometry, duplicated product, unreadable text, "
        "invented accessories, unsupported claims, fake discount, fake scarcity, misleading before-and-after, low resolution"
    )

    return ProductVideoPlan(
        score=score,
        verdict=verdict,
        reasons=tuple(reasons),
        aspect_ratio="9:16",
        duration_seconds=duration,
        creative_style=style,
        pacing=pacing,
        emphasis=emphasis,
        prompt=prompt,
        negative_prompt=negative,
    )
