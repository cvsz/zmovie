from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

TEMPLATE_CATEGORIES = (
    "product_showcase",
    "discount_alert",
    "comparison",
    "testimonial_style",
    "social_short_cut",
)

_UNSAFE_PATTERN = re.compile(
    r"(outputPath|/var/lib|file://|systemctl|process\.env|<script|javascript:|token|secret|passwd|\.ssh)",
    re.IGNORECASE,
)

# Ported from cvsz/zworkforce packages/zsp-aitool/src/lib/hyperframes/template-marketplace.ts.
# Preview assets are copied into zMovie static/images/hyperframes/.
HYPERFRAMES_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "id": "showcase-clean",
        "title": "โชว์สินค้าแบบกระชับ",
        "description": "เปิดจุดเด่นสินค้า + ราคา + คำชวนอย่างโปร่งใส",
        "category": "product_showcase",
        "tags": ["สินค้า", "จุดเด่น", "affiliate"],
        "preview_image": "/static/images/hyperframes/template-product-showcase.svg",
        "script_seed": "Hook: เริ่มด้วย pain point สั้น ๆ\nBody: แสดงสินค้าและจุดเด่นจากข้อมูลจริง\nCTA: ชวนดูรายละเอียดพร้อม disclosure ว่าเป็นลิงก์แอฟฟิลิเอต",
        "default_platform": "facebook",
        "default_aspect_ratio": "9:16",
        "default_duration_seconds": 15,
        "safety_notes": ["ห้ามอวดอ้างผลลัพธ์เกินจริง", "ใส่ affiliate disclosure ทุกครั้ง"],
    },
    {
        "id": "discount-safe",
        "title": "แจ้งโปรแบบปลอดภัย",
        "description": "เน้นส่วนลด/โปรโมชันจากข้อมูลที่ตรวจสอบได้เท่านั้น",
        "category": "discount_alert",
        "tags": ["ส่วนลด", "โปรโมชัน", "ราคา"],
        "preview_image": "/static/images/hyperframes/template-discount-alert.svg",
        "script_seed": "Hook: ระบุว่ามีโปร\nBody: บอกเงื่อนไขโปรจากข้อมูลจริง เช่น ช่วงเวลา/โค้ด\nCTA: ชวนเช็คหน้าสินค้าก่อนสั่งซื้อ",
        "default_platform": "instagram",
        "default_aspect_ratio": "1:1",
        "default_duration_seconds": 12,
        "safety_notes": ["ห้ามสร้างความเร่งด่วนปลอม", "ห้ามใช้คำรับประกันกำไร"],
    },
    {
        "id": "compare-fair",
        "title": "เปรียบเทียบแบบเป็นธรรม",
        "description": "เทียบ 2-3 ตัวเลือกตามเกณฑ์ชัดเจนโดยไม่โจมตีคู่แข่ง",
        "category": "comparison",
        "tags": ["เปรียบเทียบ", "เกณฑ์", "เลือกซื้อ"],
        "preview_image": "/static/images/hyperframes/template-comparison.svg",
        "script_seed": "Hook: นิยามปัญหาที่ผู้ชมอยากเทียบ\nBody: เทียบแต่ละตัวเลือกตามเกณฑ์เดียวกัน\nCTA: ให้ผู้ชมตัดสินใจตามการใช้งานของตัวเอง",
        "default_platform": "blog",
        "default_aspect_ratio": "16:9",
        "default_duration_seconds": 20,
        "safety_notes": ["ห้ามกล่าวอ้างอันดับดีที่สุดแบบไม่มีหลักฐาน", "เน้นข้อมูลจริงจากหน้าสินค้า"],
    },
    {
        "id": "testimonial-style-safe",
        "title": "โทนเล่าประสบการณ์อย่างปลอดภัย",
        "description": "สื่ออารมณ์คล้ายรีวิวแต่ไม่อ้างว่าเป็นลูกค้าจริง",
        "category": "testimonial_style",
        "tags": ["ประสบการณ์", "story", "safe-copy"],
        "preview_image": "/static/images/hyperframes/template-testimonial-style.svg",
        "script_seed": "Hook: เล่าบริบทการใช้งานที่พบได้ทั่วไป\nBody: อธิบายฟีเจอร์ที่อาจช่วยได้ โดยอิงข้อมูลสินค้า\nCTA: ชวนทดลองพิจารณาด้วยข้อมูลครบถ้วน",
        "default_platform": "threads",
        "default_aspect_ratio": "9:16",
        "default_duration_seconds": 18,
        "safety_notes": ["ห้ามใช้คำว่ารีวิวผู้ใช้จริง", "ห้ามสร้างผลลัพธ์ปลอม"],
    },
    {
        "id": "short-cut-social",
        "title": "คลิปสั้นลงโซเชียล",
        "description": "คัตเร็ว 3 ช่วง: Hook / Highlight / CTA",
        "category": "social_short_cut",
        "tags": ["short", "reels", "tiktok-style"],
        "preview_image": "/static/images/hyperframes/template-social-short-cut.svg",
        "script_seed": "Hook: ประโยคสั้นไม่เกิน 8 คำ\nHighlight: 2-3 จุดเด่นสำคัญ\nCTA: ชวนกดดูรายละเอียดและเปิดเผย affiliate",
        "default_platform": "x",
        "default_aspect_ratio": "9:16",
        "default_duration_seconds": 10,
        "safety_notes": ["ไม่ใส่ URL ภายนอกที่ไม่ผ่านระบบ", "ห้ามแนบโค้ดหรือคำสั่งระบบ"],
    },
)


def _assert_safe_template(template: dict[str, Any]) -> None:
    template_id = str(template.get("id") or "").strip()
    if not template_id or len(template_id) > 80:
        raise ValueError("invalid Hyperframes template id")
    category = str(template.get("category") or "")
    if category not in TEMPLATE_CATEGORIES:
        raise ValueError("invalid Hyperframes template category")
    preview = str(template.get("preview_image") or "")
    if not preview.startswith("/static/images/hyperframes/") or len(preview) > 220:
        raise ValueError("invalid Hyperframes preview image")
    duration = int(template.get("default_duration_seconds") or 0)
    if duration < 3 or duration > 120:
        raise ValueError("invalid Hyperframes default duration")
    aspect = str(template.get("default_aspect_ratio") or "")
    if aspect not in {"16:9", "9:16", "1:1"}:
        raise ValueError("invalid Hyperframes default aspect ratio")
    combined = "\n".join(
        [
            str(template.get("description") or ""),
            str(template.get("script_seed") or ""),
            *[str(item) for item in template.get("safety_notes") or []],
        ]
    )
    if _UNSAFE_PATTERN.search(combined):
        raise ValueError("unsafe Hyperframes template content")


def list_hyperframes_templates(query: str = "", category: str = "") -> list[dict[str, Any]]:
    needle = str(query or "").strip().casefold()
    category = str(category or "").strip()
    if category and category not in TEMPLATE_CATEGORIES:
        raise ValueError("unknown Hyperframes template category")
    items: list[dict[str, Any]] = []
    for raw in HYPERFRAMES_TEMPLATES:
        _assert_safe_template(raw)
        if category and raw["category"] != category:
            continue
        haystack = " ".join(
            [str(raw["title"]), str(raw["description"]), *[str(tag) for tag in raw["tags"]]]
        ).casefold()
        if needle and needle not in haystack:
            continue
        items.append(deepcopy(raw))
    return items


def get_hyperframes_template(template_id: str) -> dict[str, Any] | None:
    wanted = str(template_id or "").strip()
    for raw in HYPERFRAMES_TEMPLATES:
        if raw["id"] == wanted:
            _assert_safe_template(raw)
            return deepcopy(raw)
    return None


def apply_hyperframes_template(topic: str, template_id: str) -> tuple[str, dict[str, Any]]:
    template = get_hyperframes_template(template_id)
    if template is None:
        raise ValueError(f"Hyperframes template not found: {template_id}")
    # Reserve prompt space for the template structure and safety constraints so
    # a maximum-length operator brief cannot truncate the template guardrails.
    base = " ".join(str(topic or "").strip().split())[:3500]
    guidance = str(template["script_seed"]).strip()
    safety = "; ".join(str(item) for item in template["safety_notes"])
    enhanced = (
        f"Hyperframes template: {template['title']} ({template['category']}).\n"
        f"Creative structure:\n{guidance}\nSafety constraints: {safety}\n\n"
        f"Operator brief: {base}"
    ).strip()
    return enhanced[:5000], template
