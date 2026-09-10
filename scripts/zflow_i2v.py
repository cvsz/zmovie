#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from zmovie_platform.zflow import ZFlowComfyUIProvider, ZFlowI2VJob, product_ad_prompt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render one or more image-to-video variants through ZeaZFlow/ComfyUI")
    parser.add_argument("image", type=Path, help="Source product image")
    parser.add_argument("--count", type=int, default=3, choices=range(1, 4), metavar="1-3")
    parser.add_argument("--duration", type=int, default=5, choices=(5, 10, 20))
    parser.add_argument("--aspect-ratio", default="9:16", choices=("9:16", "16:9", "1:1", "21:9"))
    parser.add_argument("--price-mode", default="discount10", choices=("discount10", "full"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/zflow/lenovo-loq"))
    parser.add_argument("--negative-prompt", default="distorted laptop, wrong logo, warped keyboard, unreadable text, extra ports, duplicate device, low resolution")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    provider = ZFlowComfyUIProvider()
    manifest: dict[str, object] = {
        "source_image": str(args.image),
        "aspect_ratio": args.aspect_ratio,
        "duration_seconds": args.duration,
        "price_mode": args.price_mode,
        "variants": [],
    }

    for variant in range(1, args.count + 1):
        job = ZFlowI2VJob(
            source_image=args.image,
            prompt=product_ad_prompt(variant, price_mode=args.price_mode),
            negative_prompt=args.negative_prompt,
            aspect_ratio=args.aspect_ratio,
            duration_seconds=args.duration,
            output_dir=args.output_dir,
            project_id="lenovo-loq-15arp10e",
            shot_id=f"variant-{variant}",
        )
        result = provider.run_i2v(job)
        manifest["variants"].append(result)  # type: ignore[union-attr]
        print(f"variant {variant}: {result['output_path']}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
