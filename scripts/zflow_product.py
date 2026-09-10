#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from zmovie_platform.product_video import ProductProfile, assess_product
from zmovie_platform.zflow import ZFlowComfyUIProvider, ZFlowI2VJob


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assess any product and optionally render reusable 9:16 product-video variants through ZeaZFlow/ComfyUI"
    )
    parser.add_argument("product", type=Path, help="Product JSON profile")
    parser.add_argument("--image", type=Path, help="Source product image; required unless --plan-only")
    parser.add_argument("--count", type=int, default=3, choices=range(1, 4), metavar="1-3")
    parser.add_argument("--duration", type=int, choices=(5, 10, 20), help="Override generated duration")
    parser.add_argument("--aspect-ratio", choices=("9:16", "16:9", "1:1", "21:9"), help="Override generated aspect ratio")
    parser.add_argument("--output-dir", type=Path, default=Path("data/zflow/products"))
    parser.add_argument("--plan-only", action="store_true", help="Assess suitability and emit plan without rendering")
    return parser.parse_args()


def load_profile(path: Path) -> ProductProfile:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("product JSON must contain an object")
    return ProductProfile.from_dict(payload)


def main() -> int:
    args = parse_args()
    profile = load_profile(args.product)
    plan = assess_product(profile)

    manifest: dict[str, object] = {
        "product": {
            "name": profile.name,
            "brand": profile.brand,
            "category": profile.category,
        },
        "assessment": {
            "score": plan.score,
            "verdict": plan.verdict,
            "reasons": list(plan.reasons),
            "creative_style": plan.creative_style,
            "pacing": plan.pacing,
            "emphasis": list(plan.emphasis),
        },
        "generation": {
            "aspect_ratio": args.aspect_ratio or plan.aspect_ratio,
            "duration_seconds": args.duration or plan.duration_seconds,
            "count": args.count,
            "prompt": plan.prompt,
            "negative_prompt": plan.negative_prompt,
        },
        "variants": [],
    }

    slug = "-".join(profile.name.lower().split())[:64] or "product"
    output_dir = args.output_dir / slug
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.plan_only:
        manifest_path = output_dir / "plan.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        print(f"plan: {manifest_path}")
        return 0

    if args.image is None:
        raise SystemExit("--image is required unless --plan-only is used")

    provider = ZFlowComfyUIProvider()
    motions = (
        "premium controlled orbit and slow push-in",
        "energetic parallax with macro detail cuts",
        "minimal luxury turntable with clean light sweeps",
    )
    for variant in range(1, args.count + 1):
        prompt = f"{plan.prompt} Variant motion language: {motions[variant - 1]}."
        job = ZFlowI2VJob(
            source_image=args.image,
            prompt=prompt,
            negative_prompt=plan.negative_prompt,
            aspect_ratio=args.aspect_ratio or plan.aspect_ratio,
            duration_seconds=args.duration or plan.duration_seconds,
            output_dir=output_dir,
            project_id=slug,
            shot_id=f"variant-{variant}",
        )
        result = provider.run_i2v(job)
        variants = manifest["variants"]
        assert isinstance(variants, list)
        variants.append(result)
        print(f"variant {variant}: {result['output_path']}")

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
