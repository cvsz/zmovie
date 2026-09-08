from __future__ import annotations

import concurrent.futures
import os
from pathlib import Path
from typing import Any

from .media import assemble_project
from .providers import get_provider
from .qc import inspect_project
from .repository import add_asset, find_shot, get_project, list_jobs, new_job, save_job
from .storyboard import create_storyboard, production_manifest

MEDIA_ROOT = Path(os.getenv("ZMOVIE_MEDIA_ROOT", "data/media"))


def render_shot(project_id: str, shot_id: str, provider_id: str = "mock") -> dict[str, Any]:
    project = get_project(project_id)
    if project is None:
        raise ValueError("project not found")
    match = find_shot(project, shot_id)
    if match is None:
        raise ValueError("shot not found")
    _, shot = match
    provider = get_provider(provider_id)
    job = new_job(project_id, shot_id, provider_id, {"duration_seconds": shot.duration_seconds})
    job.status = "running"
    save_job(job)
    try:
        result = provider.submit(
            prompt=shot.prompt,
            negative_prompt=shot.negative_prompt,
            output_dir=MEDIA_ROOT / project.id / "renders",
            metadata={"job_id": job.id, "project_id": project.id, "shot_id": shot.id, "duration_seconds": shot.duration_seconds, "aspect_ratio": project.aspect_ratio},
        )
        job.status = str(result.get("status", "completed"))
        job.output_path = str(result.get("output_path", ""))
        job.metadata.update(result)
        save_job(job)
        if job.output_path:
            add_asset(project.id, "render", f"{shot.id} render", job.output_path, {"job_id": job.id, "provider": provider_id})
    except Exception as exc:  # Render boundary captures provider/network/ffmpeg failures.
        job.status = "failed"
        job.error = str(exc)
        save_job(job)
    return job.to_dict()


def render_project(project_id: str, provider_id: str = "mock", max_workers: int = 2) -> dict[str, Any]:
    project = get_project(project_id)
    if project is None:
        raise ValueError("project not found")
    qc = inspect_project(project)
    if not qc["passed"]:
        return {"status": "blocked", "reason": "quality-control", "qc": qc, "jobs": []}
    shot_ids = [shot.id for scene in project.scenes for shot in scene.shots]
    workers = max(1, min(int(max_workers), 8))
    jobs: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(render_shot, project_id, shot_id, provider_id) for shot_id in shot_ids]
        for future in concurrent.futures.as_completed(futures):
            jobs.append(future.result())
    failed = [job for job in jobs if job["status"] == "failed"]
    return {"status": "failed" if failed else "completed", "jobs": jobs, "failed": len(failed)}


def assemble_from_jobs(project_id: str) -> dict[str, Any]:
    project = get_project(project_id)
    if project is None:
        raise ValueError("project not found")
    jobs = [item for item in list_jobs(project_id, limit=1000) if item["status"] == "completed" and item.get("output_path")]
    # Preserve storyboard order, selecting the newest completed output for each shot.
    by_shot: dict[str, str] = {}
    for job in jobs:
        by_shot.setdefault(job["shot_id"], job["output_path"])
    clips = [by_shot[shot.id] for scene in project.scenes for shot in scene.shots if shot.id in by_shot]
    result = assemble_project(project, clips)
    add_asset(project.id, "final", "assembled movie", result["output_path"], result)
    return result


def run_end_to_end(
    *,
    name: str,
    concept: str,
    genre: str = "action",
    visual_style: str = "photorealistic premium cinematic realism",
    aspect_ratio: str = "16:9",
    target_duration_seconds: int = 60,
    provider: str = "mock",
    owner: str = "local",
) -> dict[str, Any]:
    from .repository import save_project

    project = create_storyboard(
        name=name,
        concept=concept,
        genre=genre,
        visual_style=visual_style,
        aspect_ratio=aspect_ratio,
        target_duration_seconds=target_duration_seconds,
        owner=owner,
    )
    save_project(project)
    qc = inspect_project(project)
    render = render_project(project.id, provider)
    assembly = assemble_from_jobs(project.id) if render["status"] == "completed" else None
    return {
        "project": project.to_dict(),
        "manifest": production_manifest(project),
        "qc": qc,
        "render": render,
        "assembly": assembly,
    }
