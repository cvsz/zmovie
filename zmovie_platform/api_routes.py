from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse

from .api_schemas import AssetRequest, BootstrapRequest, LoginRequest, PipelineRequest, RenderRequest, StoryboardRequest
from .audit import write as audit
from .auth import authenticate, bootstrap_admin_from_env, create_user, decode_token, issue_token, user_count
from .backup import create_backup
from .config import settings
from .exporter import export_project
from .health import health_report
from .jobs import submit
from .metrics import increment, snapshot
from .pipeline import assemble_from_jobs, render_project, render_shot, run_end_to_end
from .presets import PRESETS
from .providers import provider_specs
from .qc import director_notes, inspect_project
from .repository import add_asset, delete_project, get_job, get_project, list_assets, list_jobs, list_projects, save_project
from .storyboard import create_storyboard, production_manifest, regenerate_project_prompts

router = APIRouter(prefix="/api/v2")
EXPORT_ROOT = Path(os.getenv("ZMOVIE_EXPORT_ROOT", "data/exports"))

# First-run native/container installations can provision an admin through env.
bootstrap_admin_from_env()


def current_actor(authorization: str | None = Header(default=None)) -> dict[str, str]:
    if not settings.auth_enabled:
        return {"username": "local", "role": "admin"}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="authentication required", headers={"WWW-Authenticate": "Bearer"})
    payload = decode_token(authorization.split(" ", 1)[1].strip())
    if payload is None:
        raise HTTPException(status_code=401, detail="invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    return {"username": str(payload.get("sub", "unknown")), "role": str(payload.get("role", "user"))}


def require_project(project_id: str, actor: dict[str, str]) -> Any:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    if settings.auth_enabled and actor.get("role") != "admin" and project.owner != actor.get("username"):
        raise HTTPException(status_code=403, detail="project access denied")
    return project


@router.get("/health", tags=["system"])
def v2_health() -> dict[str, object]:
    return health_report()


@router.get("/capabilities", tags=["system"])
def capabilities() -> dict[str, object]:
    return {
        "version": "2.0.0",
        "auth_enabled": settings.auth_enabled,
        "auth_bootstrap_required": settings.auth_enabled and user_count() == 0,
        "providers": provider_specs(),
        "presets": PRESETS,
        "features": [
            "projects", "character-bible", "storyboard", "continuity-locks", "production-manifest",
            "quality-control", "director-notes", "render-jobs", "mock-renderer", "webhook-renderer",
            "asset-library", "ffmpeg-assembly", "production-export", "local-auth", "audit", "backup", "metrics",
        ],
    }


@router.get("/metrics", tags=["system"])
def metrics(actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    return snapshot()


@router.post("/auth/bootstrap", tags=["auth"])
def bootstrap(payload: BootstrapRequest) -> dict[str, object]:
    if not settings.auth_enabled:
        return {"auth_enabled": False, "message": "authentication is disabled"}
    if user_count() != 0:
        raise HTTPException(status_code=409, detail="bootstrap is already complete")
    try:
        user = create_user(payload.username, payload.password, "admin")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    audit("auth.bootstrap", actor=user["username"])
    return {"user": user, "token": issue_token(user)}


@router.post("/auth/login", tags=["auth"])
def login(payload: LoginRequest) -> dict[str, object]:
    user = authenticate(payload.username, payload.password)
    if user is None:
        increment("auth.login_failed")
        raise HTTPException(status_code=401, detail="invalid credentials")
    increment("auth.login_success")
    audit("auth.login", actor=user["username"])
    return {"user": user, "token": issue_token(user)}


@router.get("/projects", tags=["projects"])
def projects(actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    owner = None if actor.get("role") == "admin" else actor["username"]
    return {"items": list_projects(owner=owner)}


@router.post("/projects", tags=["projects"])
def create_project(payload: StoryboardRequest, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    project = create_storyboard(
        name=payload.name,
        concept=payload.concept,
        genre=payload.genre,
        visual_style=payload.visual_style,
        aspect_ratio=payload.aspect_ratio,
        target_duration_seconds=payload.target_duration_seconds,
        scene_count=payload.scene_count,
        owner=actor["username"],
    )
    save_project(project)
    increment("projects.created")
    audit("project.create", actor=actor["username"], project_id=project.id)
    return {"project": project.to_dict(), "qc": inspect_project(project), "director_notes": director_notes(project)}


@router.get("/projects/{project_id}", tags=["projects"])
def project_detail(project_id: str, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    project = require_project(project_id, actor)
    return {"project": project.to_dict(), "qc": inspect_project(project), "director_notes": director_notes(project)}


@router.delete("/projects/{project_id}", tags=["projects"])
def remove_project(project_id: str, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    project = require_project(project_id, actor)
    deleted = delete_project(project.id)
    audit("project.delete", actor=actor["username"], project_id=project.id)
    return {"deleted": deleted, "project_id": project.id}


@router.post("/projects/{project_id}/regenerate", tags=["projects"])
def regenerate(project_id: str, seed: int | None = None, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    project = require_project(project_id, actor)
    regenerate_project_prompts(project, seed=seed)
    save_project(project)
    increment("projects.regenerated")
    audit("project.regenerate", actor=actor["username"], project_id=project.id, seed=seed)
    return {"project": project.to_dict(), "qc": inspect_project(project)}


@router.get("/projects/{project_id}/manifest", tags=["projects"])
def manifest(project_id: str, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    return production_manifest(require_project(project_id, actor))


@router.get("/projects/{project_id}/qc", tags=["projects"])
def qc(project_id: str, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    return inspect_project(require_project(project_id, actor))


@router.post("/projects/{project_id}/shots/{shot_id}/render", tags=["render"])
def start_shot_render(project_id: str, shot_id: str, payload: RenderRequest, background: BackgroundTasks, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    project = require_project(project_id, actor)
    if not any(shot.id == shot_id for scene in project.scenes for shot in scene.shots):
        raise HTTPException(status_code=404, detail="shot not found")
    # Execute after the response so provider latency does not block the request.
    background.add_task(render_shot, project_id, shot_id, payload.provider)
    increment("render.shot_queued")
    audit("render.shot_queue", actor=actor["username"], project_id=project_id, shot_id=shot_id, provider=payload.provider)
    return {"status": "queued", "project_id": project_id, "shot_id": shot_id, "provider": payload.provider}


@router.post("/projects/{project_id}/render", tags=["render"])
def start_project_render(project_id: str, payload: RenderRequest, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    project = require_project(project_id, actor)
    report = inspect_project(project)
    if not report["passed"]:
        raise HTTPException(status_code=409, detail={"message": "project failed QC", "qc": report})
    submit(render_project, project_id, payload.provider, payload.max_workers)
    increment("render.project_queued")
    audit("render.project_queue", actor=actor["username"], project_id=project_id, provider=payload.provider)
    return {"status": "queued", "project_id": project_id, "provider": payload.provider}


@router.get("/projects/{project_id}/jobs", tags=["render"])
def project_jobs(project_id: str, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    require_project(project_id, actor)
    return {"items": list_jobs(project_id)}


@router.get("/jobs/{job_id}", tags=["render"])
def job_detail(job_id: str, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    require_project(job.project_id, actor)
    return job.to_dict()


@router.post("/projects/{project_id}/assemble", tags=["render"])
def assemble(project_id: str, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    require_project(project_id, actor)
    try:
        result = assemble_from_jobs(project_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    increment("assembly.completed")
    audit("project.assemble", actor=actor["username"], project_id=project_id, status=result.get("status"))
    return result


@router.get("/projects/{project_id}/assets", tags=["assets"])
def assets(project_id: str, kind: str | None = None, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    require_project(project_id, actor)
    return {"items": list_assets(project_id, kind)}


@router.post("/projects/{project_id}/assets", tags=["assets"])
def create_asset(project_id: str, payload: AssetRequest, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    require_project(project_id, actor)
    result = add_asset(project_id, payload.kind, payload.name, payload.path)
    audit("asset.create", actor=actor["username"], project_id=project_id, asset_id=result["id"])
    return result


@router.post("/projects/{project_id}/export", tags=["projects"])
def export(project_id: str, actor: dict[str, str] = Depends(current_actor)) -> FileResponse:
    project = require_project(project_id, actor)
    archive = export_project(project, EXPORT_ROOT)
    audit("project.export", actor=actor["username"], project_id=project_id)
    return FileResponse(path=archive, filename=archive.name, media_type="application/zip")


@router.post("/admin/backup", tags=["system"])
def backup(actor: dict[str, str] = Depends(current_actor)) -> dict[str, str]:
    if actor.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    target = create_backup()
    audit("backup.create", actor=actor["username"], path=str(target))
    return {"status": "completed", "path": str(target)}


@router.post("/pipeline", tags=["render"])
def pipeline(payload: PipelineRequest, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    increment("pipeline.started")
    result = run_end_to_end(
        name=payload.name,
        concept=payload.concept,
        genre=payload.genre,
        visual_style=payload.visual_style,
        aspect_ratio=payload.aspect_ratio,
        target_duration_seconds=payload.target_duration_seconds,
        provider=payload.provider,
        owner=actor["username"],
    )
    increment("pipeline.completed" if result["render"]["status"] == "completed" else "pipeline.failed")
    audit("pipeline.run", actor=actor["username"], project_id=result["project"]["id"], provider=payload.provider)
    return result
