from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .api_routes import current_actor, require_project
from .api_schemas import BilibiliPrepareRequest
from .audit import write as audit
from .content_storyboard import create_content_storyboard
from .hyperframes import get_hyperframes_template, list_hyperframes_templates
from .jobs import submit
from .metrics import increment
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
from .repository import list_jobs

router = APIRouter(prefix="/api/v2")


class ContentStoryboardRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=5000)
    name: str = Field(default="", max_length=200)
    audience: str = Field(default="general audience", max_length=300)
    goal: str = Field(default="engagement", max_length=300)
    tone: str = Field(default="cinematic, premium and clear", max_length=300)
    brand: str = Field(default="", max_length=200)
    call_to_action: str = Field(default="", max_length=500)
    genre: str = Field(default="commercial", max_length=80)
    visual_style: str = Field(default="photorealistic premium cinematic realism", max_length=500)
    aspect_ratio: str = Field(default="16:9", max_length=20)
    target_duration_seconds: int = Field(default=60, ge=10, le=3600)
    scene_count: int | None = Field(default=None, ge=1, le=24)
    seed: int | None = None
    template_id: str = Field(default="", max_length=80)


class ProductionRenderRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    max_workers: int = Field(default=2, ge=1, le=8)


class ProductionRunRequest(ProductionRenderRequest):
    title: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=10)
    playlist: str = Field(default="", max_length=200)
    content_type: str = Field(default="Original", pattern="^(Original|Repost)$")
    schedule_at: str = Field(default="", max_length=80)


def _public_run(run: dict[str, Any] | None) -> dict[str, Any] | None:
    if run is None:
        return None
    return {
        key: run.get(key)
        for key in (
            "id",
            "project_id",
            "provider",
            "max_workers",
            "status",
            "stage",
            "publish_job_id",
            "error",
            "created_at",
            "updated_at",
        )
    }


def _ensure_no_active_render(project_id: str) -> None:
    if any(str(job.get("status")) in {"queued", "running"} for job in list_jobs(project_id, limit=5000)):
        raise HTTPException(status_code=409, detail="project already has active render jobs")


def _require_ready_provider_from_state(state: dict[str, Any], provider_id: str) -> None:
    ready = {str(item.get("id") or "") for item in state.get("providers", []) if isinstance(item, dict)}
    if provider_id in ready:
        return
    blocked = next(
        (
            item
            for item in state.get("blocked_providers", [])
            if isinstance(item, dict) and str(item.get("id") or "") == provider_id
        ),
        None,
    )
    if blocked is not None:
        reasons = ", ".join(str(item) for item in blocked.get("reasons") or [])
        raise HTTPException(
            status_code=409,
            detail=(
                f"production render provider is configured but not production-ready: {provider_id}; "
                f"{reasons or 'runtime readiness failed'}. Run 'sudo zmovie-ctl doctor'."
            ),
        )
    raise HTTPException(status_code=409, detail=f"production render provider is not configured: {provider_id}")


@router.get("/hyperframes/templates", tags=["production"])
def hyperframes_templates(
    query: str = "",
    category: str = "",
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    del actor
    try:
        items = list_hyperframes_templates(query=query, category=category)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"count": len(items), "items": items}


@router.get("/hyperframes/templates/{template_id}", tags=["production"])
def hyperframes_template(
    template_id: str,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    del actor
    item = get_hyperframes_template(template_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Hyperframes template not found")
    return item


@router.post("/content/storyboard", tags=["production"])
def one_click_content_storyboard(
    payload: ContentStoryboardRequest,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    try:
        result = create_content_storyboard(
            topic=payload.topic,
            name=payload.name,
            audience=payload.audience,
            goal=payload.goal,
            tone=payload.tone,
            brand=payload.brand,
            call_to_action=payload.call_to_action,
            genre=payload.genre,
            visual_style=payload.visual_style,
            aspect_ratio=payload.aspect_ratio,
            target_duration_seconds=payload.target_duration_seconds,
            scene_count=payload.scene_count,
            seed=payload.seed,
            owner=actor["username"],
            template_id=payload.template_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    project_id = str(result["project"]["id"])
    increment("content.storyboard.generated")
    audit(
        "content.storyboard.generate",
        actor=actor["username"],
        project_id=project_id,
        hyperframes_template=payload.template_id,
    )
    return result


@router.get("/projects/{project_id}/production/readiness", tags=["production"])
def readiness(project_id: str, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    require_project(project_id, actor)
    try:
        return production_readiness(project_id)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/projects/{project_id}/production/render", tags=["production"])
def production_render(
    project_id: str,
    payload: ProductionRenderRequest,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    require_project(project_id, actor)
    state = production_readiness(project_id)
    _require_ready_provider_from_state(state, payload.provider)
    if not state["qc"]["passed"]:
        raise HTTPException(status_code=409, detail={"message": "project failed QC", "qc": state["qc"]})
    _ensure_no_active_render(project_id)
    submit(render_all_production, project_id, payload.provider, payload.max_workers)
    increment("production.render.queued")
    audit("production.render.queue", actor=actor["username"], project_id=project_id, provider=payload.provider)
    return {"status": "queued", "project_id": project_id, "provider": payload.provider, "production": True}


@router.post("/projects/{project_id}/production/assemble", tags=["production"])
def production_assemble(project_id: str, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    require_project(project_id, actor)
    try:
        result = assemble_production(project_id)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    increment("production.assembly.completed")
    audit("production.assemble", actor=actor["username"], project_id=project_id)
    return result


@router.post("/projects/{project_id}/production/publish/bilibili/prepare", tags=["production", "publish"])
def production_prepare_bilibili(
    project_id: str,
    payload: BilibiliPrepareRequest,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    require_project(project_id, actor)
    try:
        job = prepare_bilibili_production(
            project_id,
            title=payload.title,
            description=payload.description,
            tags=payload.tags or None,
            playlist=payload.playlist,
            content_type=payload.content_type,
            schedule_at=payload.schedule_at,
        )
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    increment("production.publish.bilibili.prepared")
    audit("production.publish.bilibili.prepare", actor=actor["username"], project_id=project_id, job_id=job.get("id"))
    return {
        key: job[key]
        for key in (
            "id",
            "project_id",
            "platform",
            "status",
            "title",
            "description",
            "tags",
            "playlist",
            "content_type",
            "schedule_at",
            "published_url",
            "error",
            "metadata",
            "created_at",
            "updated_at",
        )
        if key in job
    }


@router.post("/projects/{project_id}/production/export", tags=["production"])
def production_export(project_id: str, actor: dict[str, str] = Depends(current_actor)) -> FileResponse:
    project = require_project(project_id, actor)
    try:
        archive = export_production_package(project.id)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    increment("production.export.completed")
    audit("production.export", actor=actor["username"], project_id=project_id)
    return FileResponse(path=archive, filename=archive.name, media_type="application/zip")


@router.post("/projects/{project_id}/production/run", tags=["production"])
def production_run(
    project_id: str,
    payload: ProductionRunRequest,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    require_project(project_id, actor)
    _ensure_no_active_render(project_id)
    try:
        run = start_production_run(
            project_id,
            payload.provider,
            payload.max_workers,
            {
                "title": payload.title,
                "description": payload.description,
                "tags": payload.tags,
                "playlist": payload.playlist,
                "content_type": payload.content_type,
                "schedule_at": payload.schedule_at,
            },
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    submit(execute_production_run, project_id, str(run["id"]))
    increment("production.run.queued")
    audit("production.run.queue", actor=actor["username"], project_id=project_id, run_id=run["id"], provider=payload.provider)
    return _public_run(run) or {}


@router.get("/projects/{project_id}/production/run", tags=["production"])
def production_run_latest(project_id: str, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    require_project(project_id, actor)
    return {"run": _public_run(latest_production_run(project_id))}


@router.get("/projects/{project_id}/production/runs/{run_id}", tags=["production"])
def production_run_status(
    project_id: str,
    run_id: str,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    require_project(project_id, actor)
    run = get_production_run(project_id, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="production run not found")
    return _public_run(run) or {}
