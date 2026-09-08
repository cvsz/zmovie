from __future__ import annotations

import argparse
import json

from .pipeline import run_end_to_end
from .providers import provider_specs
from .qc import inspect_project
from .repository import get_project, list_projects
from .storyboard import production_manifest


def main() -> int:
    parser = argparse.ArgumentParser(prog="zmovie-platform")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("run", help="run concept-to-assembly pipeline")
    create.add_argument("--name", default="Untitled zMovie")
    create.add_argument("--concept", required=True)
    create.add_argument("--genre", default="action")
    create.add_argument("--style", default="photorealistic premium cinematic realism")
    create.add_argument("--aspect-ratio", default="16:9")
    create.add_argument("--duration", type=int, default=60)
    create.add_argument("--provider", default="mock")

    sub.add_parser("providers", help="list render providers")
    sub.add_parser("projects", help="list projects")
    inspect = sub.add_parser("inspect", help="inspect a project")
    inspect.add_argument("project_id")

    args = parser.parse_args()
    if args.command == "run":
        result = run_end_to_end(name=args.name, concept=args.concept, genre=args.genre, visual_style=args.style, aspect_ratio=args.aspect_ratio, target_duration_seconds=args.duration, provider=args.provider)
    elif args.command == "providers":
        result = provider_specs()
    elif args.command == "projects":
        result = list_projects()
    else:
        project = get_project(args.project_id)
        if project is None:
            parser.error("project not found")
        result = {"project": production_manifest(project), "qc": inspect_project(project)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
