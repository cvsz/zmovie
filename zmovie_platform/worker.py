from __future__ import annotations

import argparse
import json
import time

from .pipeline import render_shot
from .repository import get_job


def main() -> int:
    parser = argparse.ArgumentParser(description="zMovie render worker helper")
    parser.add_argument("project_id")
    parser.add_argument("shot_id")
    parser.add_argument("--provider", default="mock")
    args = parser.parse_args()
    result = render_shot(args.project_id, args.shot_id, args.provider)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
