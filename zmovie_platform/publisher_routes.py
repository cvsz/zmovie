from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from .api_routes import current_actor, require_project
from .api_schemas import BilibiliPrepareRequest, BilibiliPublishRequest
from .audit import write as audit
from .jobs import submit
from .metrics import increment
from .publishers.bilibili_hardened import (
    approve_publish_job,
    get_publish_job,
    list_publish_jobs,
    prepare_bilibili_publish,
    publish_bilibili_job,
    session_status,
)

router = APIRouter(prefix="/api/v2")

_PUBLIC_PUBLISH_JOB_FIELDS = (
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


def _public_publish_job(job: dict[str, object]) -> dict[str, object]:
    return {field: job[field] for field in _PUBLIC_PUBLISH_JOB_FIELDS if field in job}


def _public_session_status(status: dict[str, object]) -> dict[str, object]:
    result = {
        field: status[field]
        for field in ("configured", "authenticated", "checked", "headless", "studio_url")
        if field in status
    }
    if status.get("error"):
        result["error"] = "session_probe_failed"
    return result


def _require_publish_job(job_id: str, actor: dict[str, str]) -> dict[str, object]:
    job = get_publish_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="publish job not found")
    require_project(str(job["project_id"]), actor)
    return job


@router.get("/publish/bilibili/session", tags=["publish"])
def bilibili_session(actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    return _public_session_status(session_status())


@router.get("/publish/jobs", tags=["publish"])
def publish_jobs(project_id: str | None = None, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    items = list_publish_jobs(project_id=project_id)
    if actor.get("role") == "admin":
        return {"items": [_public_publish_job(item) for item in items]}
    allowed: list[dict[str, object]] = []
    for item in items:
        try:
            require_project(str(item["project_id"]), actor)
            allowed.append(_public_publish_job(item))
        except HTTPException:
            continue
    return {"items": allowed}


@router.get("/publish/jobs/{job_id}", tags=["publish"])
def publish_job(job_id: str, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    return _public_publish_job(_require_publish_job(job_id, actor))


@router.post("/projects/{project_id}/publish/bilibili/prepare", tags=["publish"])
def prepare_bilibili(project_id: str, payload: BilibiliPrepareRequest, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    require_project(project_id, actor)
    try:
        # The public API intentionally does not accept arbitrary filesystem paths.
        # The final video is selected from managed project assets, the cover is
        # generated into the publish root, and subtitles must be attached through
        # managed application workflows rather than a request-provided server path.
        job = prepare_bilibili_publish(
            project_id,
            title=payload.title,
            description=payload.description,
            tags=payload.tags or None,
            playlist=payload.playlist,
            content_type=payload.content_type,
            schedule_at=payload.schedule_at,
        )
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    increment("publish.bilibili.prepared")
    audit("publish.bilibili.prepare", actor=actor["username"], project_id=project_id, job_id=job.get("id"))
    return _public_publish_job(job)


@router.post("/publish/jobs/{job_id}/approve", tags=["publish"])
def approve_bilibili(job_id: str, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    _require_publish_job(job_id, actor)
    try:
        job = approve_publish_job(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    increment("publish.bilibili.approved")
    audit("publish.bilibili.approve", actor=actor["username"], project_id=str(job["project_id"]), job_id=job_id)
    return _public_publish_job(job)


@router.post("/publish/jobs/{job_id}/publish", tags=["publish"])
def publish_bilibili(job_id: str, payload: BilibiliPublishRequest, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    job = _require_publish_job(job_id, actor)
    if str(job["status"]) != "approved":
        raise HTTPException(status_code=409, detail="publish job must be approved before publishing")
    session = session_status()
    if not session.get("authenticated"):
        raise HTTPException(status_code=409, detail="Bilibili browser session is missing, expired, or not authenticated; run the one-time Google login and validate the session first")
    submit(publish_bilibili_job, job_id, headless=payload.headless)
    increment("publish.bilibili.queued")
    audit("publish.bilibili.queue", actor=actor["username"], project_id=str(job["project_id"]), job_id=job_id)
    return {"status": "queued", "job_id": job_id, "platform": "bilibili_tv"}
