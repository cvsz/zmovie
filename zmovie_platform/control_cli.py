from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .content_storyboard import create_content_storyboard
from .production import (
    assemble_production,
    execute_production_run,
    export_production_package,
    get_production_run,
    latest_production_run,
    prepare_bilibili_production,
    production_readiness,
    render_all_production,
    start_production_run,
)
from .providers import provider_specs
from .publishers import bilibili_hardened, bilibili_preflight, bilibili_ui_compat
from .repository import list_jobs, list_projects


def _emit(value: Any) -> None:
    if isinstance(value, Path):
        value = {"path": str(value)}
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _ensure_no_active_render(project_id: str) -> None:
    active = [
        item
        for item in list_jobs(project_id, limit=5000)
        if str(item.get("status") or "") in {"queued", "running"}
    ]
    if active:
        raise RuntimeError(f"project already has {len(active)} active render job(s)")


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _add_bilibili_fields(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--tags", default="")
    parser.add_argument("--playlist", default="")
    parser.add_argument("--content-type", choices=("Original", "Repost"), default="Original")
    parser.add_argument("--schedule-at", default="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zmovie-control",
        description="Local production control plane for a zMovie installation.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("providers", help="list render providers and configuration state")
    sub.add_parser("projects", help="list projects")

    readiness = sub.add_parser("readiness", help="show strict production readiness")
    readiness.add_argument("project_id")

    content = sub.add_parser("content", help="generate content strategy and storyboard in one step")
    content.add_argument("--topic", required=True)
    content.add_argument("--name", default="")
    content.add_argument("--audience", default="general audience")
    content.add_argument("--goal", default="engagement")
    content.add_argument("--tone", default="cinematic, premium and clear")
    content.add_argument("--brand", default="")
    content.add_argument("--call-to-action", default="")
    content.add_argument("--genre", default="commercial")
    content.add_argument("--style", default="photorealistic premium cinematic realism")
    content.add_argument("--aspect-ratio", default="16:9")
    content.add_argument("--duration", type=int, default=60)
    content.add_argument("--scene-count", type=int, default=None)
    content.add_argument("--seed", type=int, default=None)
    content.add_argument("--owner", default="local")

    render = sub.add_parser("render", help="render all shots using a real configured provider")
    render.add_argument("project_id")
    render.add_argument("--provider", required=True)
    render.add_argument("--workers", type=int, default=2)

    assemble = sub.add_parser("assemble", help="strictly assemble a validated final video")
    assemble.add_argument("project_id")

    prepare = sub.add_parser("prepare-bilibili", help="prepare a Bilibili package from the validated final")
    prepare.add_argument("project_id")
    _add_bilibili_fields(prepare)

    export = sub.add_parser("export", help="build the portable production ZIP with checksums")
    export.add_argument("project_id")

    production = sub.add_parser(
        "production",
        help="run render -> validate -> assemble -> prepare Bilibili -> export; stops at approval gate",
    )
    production.add_argument("project_id")
    production.add_argument("--provider", required=True)
    production.add_argument("--workers", type=int, default=2)
    _add_bilibili_fields(production)

    run_status = sub.add_parser("run-status", help="show latest or exact production run state")
    run_status.add_argument("project_id")
    run_status.add_argument("--run-id", default="")

    session = sub.add_parser("bili-session", help="check Bilibili Creator Center session")
    session.add_argument("--no-probe", action="store_true")

    bili_status = sub.add_parser("bili-status", help="show a Bilibili publish job")
    bili_status.add_argument("job_id")

    bili_approve = sub.add_parser("bili-approve", help="record human approval for an exact publish package")
    bili_approve.add_argument("job_id")
    bili_approve.add_argument("--confirm", required=True)

    bili_publish = sub.add_parser("bili-publish", help="run fail-closed preflight and one real Bilibili submission")
    bili_publish.add_argument("job_id")
    bili_publish.add_argument("--confirm", required=True)

    return parser


def _bilibili_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "title": args.title,
        "description": args.description,
        "tags": _csv(args.tags),
        "playlist": args.playlist,
        "content_type": args.content_type,
        "schedule_at": args.schedule_at,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "providers":
            result: Any = provider_specs()
        elif args.command == "projects":
            result = list_projects(limit=500)
        elif args.command == "readiness":
            result = production_readiness(args.project_id)
        elif args.command == "content":
            result = create_content_storyboard(
                topic=args.topic,
                name=args.name,
                audience=args.audience,
                goal=args.goal,
                tone=args.tone,
                brand=args.brand,
                call_to_action=args.call_to_action,
                genre=args.genre,
                visual_style=args.style,
                aspect_ratio=args.aspect_ratio,
                target_duration_seconds=args.duration,
                scene_count=args.scene_count,
                seed=args.seed,
                owner=args.owner,
            )
        elif args.command == "render":
            _ensure_no_active_render(args.project_id)
            result = render_all_production(args.project_id, args.provider, args.workers)
        elif args.command == "assemble":
            result = assemble_production(args.project_id)
        elif args.command == "prepare-bilibili":
            result = prepare_bilibili_production(args.project_id, **_bilibili_payload(args))
        elif args.command == "export":
            result = export_production_package(args.project_id)
        elif args.command == "production":
            _ensure_no_active_render(args.project_id)
            run = start_production_run(
                args.project_id,
                args.provider,
                args.workers,
                _bilibili_payload(args),
            )
            result = execute_production_run(args.project_id, str(run["id"]))
        elif args.command == "run-status":
            if args.run_id:
                result = get_production_run(args.project_id, args.run_id)
                if result is None:
                    raise ValueError("production run not found")
            else:
                result = latest_production_run(args.project_id)
                if result is None:
                    raise ValueError("no production run found")
        elif args.command == "bili-session":
            result = bilibili_hardened.session_status(probe=not args.no_probe)
        elif args.command == "bili-status":
            result = bilibili_hardened.get_publish_job(args.job_id)
            if result is None:
                raise ValueError("publish job not found")
        elif args.command == "bili-approve":
            if args.confirm != "APPROVE":
                raise ValueError("approval requires --confirm APPROVE")
            result = bilibili_hardened.approve_publish_job(args.job_id)
        elif args.command == "bili-publish":
            if args.confirm != "CONFIRM-PUBLISH":
                raise ValueError("external publication requires --confirm CONFIRM-PUBLISH")
            session = bilibili_hardened.session_status(probe=True)
            if not session.get("authenticated"):
                raise RuntimeError("Bilibili session is not authenticated")
            preflight = bilibili_preflight.preflight_publish_job(args.job_id)
            if not preflight.get("ready"):
                raise RuntimeError("Bilibili preflight did not report ready=true")
            result = bilibili_ui_compat.publish_bilibili_job(args.job_id, headless=True)
        else:
            parser.error("unsupported command")
            return 2
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        parser.exit(2, f"zmovie-control: error: {exc}\n")

    _emit(result)
    if isinstance(result, dict) and str(result.get("status") or "") == "failed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
