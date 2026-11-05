from __future__ import annotations

import ipaddress
import os
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from .api_schemas import AssetRequest, BootstrapRequest, LoginRequest, PipelineRequest, RenderRequest, StoryboardRequest
from .audit import write as audit
from .auth import authenticate, create_first_admin, decode_token, issue_token, user_count
from .backup import create_backup
from .config import is_loopback_host, settings
from .exporter import export_project
from .health import public_health_report
from .jobs import submit
from .metrics import increment, snapshot
from .oauth import OAuthManager, build_oauth_manager_from_env, find_or_create_oauth_user
from .pipeline import assemble_from_jobs, render_project, render_shot, run_end_to_end
from .presets import PRESETS
from .providers import provider_specs
from .qc import director_notes, inspect_project
from .rate_limit import allowed
from .repository import (
    add_asset,
    delete_project,
    get_job,
    get_project,
    list_assets,
    list_jobs,
    list_projects,
    save_project,
)
from .security import validate_managed_asset_path
from .storage import connect
from .storyboard import create_storyboard, production_manifest, regenerate_project_prompts

router = APIRouter(prefix="/api/v2")
EXPORT_ROOT = Path(os.getenv("ZMOVIE_EXPORT_ROOT", "data/exports"))

# OAuth manager (lazy init from env)
_oauth_manager: OAuthManager | None = None


def get_oauth_manager() -> OAuthManager:
    global _oauth_manager
    if _oauth_manager is None:
        _oauth_manager = build_oauth_manager_from_env()
    return _oauth_manager


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


def _enforce_rate_limit(request: Request, *, name: str, limit: int) -> None:
    host = request.client.host if request.client else "unknown"
    if not allowed(f"{name}:{host}", limit=limit, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="rate limit exceeded",
            headers={"Retry-After": "60"},
        )


def oauth_base_url(request: Request) -> str:
    configured = settings.base_url.strip().rstrip("/")
    if not configured:
        peer = request.client.host if request.client else ""
        try:
            peer_is_loopback = ipaddress.ip_address(peer).is_loopback
        except ValueError:
            peer_is_loopback = False
        if not is_loopback_host(request.url.hostname or "") or not peer_is_loopback:
            raise HTTPException(status_code=503, detail="OAuth requires ZMOVIE_BASE_URL on a public host")
        return str(request.base_url).rstrip("/")

    try:
        parsed = urlsplit(configured)
        hostname = parsed.hostname or ""
        parsed.port
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="ZMOVIE_BASE_URL is invalid") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or (not is_loopback_host(hostname) and parsed.scheme != "https")
    ):
        raise HTTPException(status_code=503, detail="ZMOVIE_BASE_URL is invalid")
    return configured


@router.get("/health", tags=["system"])
def v2_health() -> dict[str, object]:
    return public_health_report()


@router.get("/livez", tags=["system"], include_in_schema=False)
def livez() -> dict[str, object]:
    """Liveness: กระบวนการยังทำงานอยู่ (ไม่แตะ DB/disk)."""
    return {"status": "alive"}


@router.get("/readyz", tags=["system"], include_in_schema=False)
def readyz() -> dict[str, object]:
    """Readiness: DB + migrations พร้อมรับงานหรือไม่."""
    from .migrations import migrate

    try:
        migrate()
        count = user_count()
    except Exception as exc:  # noqa: BLE001 - readiness ต้องรายงานทุกความล้มเหลว
        raise HTTPException(status_code=503, detail="not ready") from exc
    return {"status": "ready", "users": count}


@router.get("/capabilities", tags=["system"])
def capabilities() -> dict[str, object]:
    oauth_providers = []
    if settings.auth_enabled and settings.oauth_enabled:
        try:
            mgr = get_oauth_manager()
            oauth_providers = mgr.list_providers()
        except Exception:
            pass
    return {
        "version": "2.0.0",
        "auth_enabled": settings.auth_enabled,
        "auth_bootstrap_required": settings.auth_enabled and user_count() == 0,
        "oauth_enabled": settings.auth_enabled and settings.oauth_enabled,
        "oauth_providers": oauth_providers,
        "providers": provider_specs(),
        "presets": PRESETS,
        "features": [
            "projects", "character-bible", "storyboard", "continuity-locks", "production-manifest",
            "quality-control", "director-notes", "render-jobs", "mock-renderer", "webhook-renderer",
            "asset-library", "ffmpeg-assembly", "production-export", "local-auth", "audit", "backup", "metrics",
            "oauth",
        ],
    }


@router.get("/metrics", tags=["system"])
def metrics(actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    return snapshot()


@router.post("/auth/bootstrap", tags=["auth"])
def bootstrap(payload: BootstrapRequest, request: Request) -> dict[str, object]:
    _enforce_rate_limit(request, name="auth-bootstrap", limit=5)
    if not settings.auth_enabled:
        return {"auth_enabled": False, "message": "authentication is disabled"}
    peer = request.client.host if request.client else ""
    try:
        peer_is_loopback = ipaddress.ip_address(peer).is_loopback
    except ValueError:
        peer_is_loopback = False
    if not is_loopback_host(settings.host) or not peer_is_loopback:
        raise HTTPException(status_code=403, detail="bootstrap is available only over a loopback connection")
    try:
        user = create_first_admin(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if user is None:
        raise HTTPException(status_code=409, detail="bootstrap is already complete")
    audit("auth.bootstrap", actor=user["username"])
    return {"user": user, "token": issue_token(user)}


@router.post("/auth/login", tags=["auth"])
def login(payload: LoginRequest, request: Request) -> dict[str, object]:
    _enforce_rate_limit(request, name="auth-login", limit=10)
    user = authenticate(payload.username, payload.password)
    if user is None:
        increment("auth.login_failed")
        raise HTTPException(status_code=401, detail="invalid credentials")
    increment("auth.login_success")
    audit("auth.login", actor=user["username"])
    return {"user": user, "token": issue_token(user)}


@router.get("/auth/oauth/providers", tags=["auth"])
def oauth_providers() -> dict[str, object]:
    """List configured OAuth providers."""
    if not settings.auth_enabled or not settings.oauth_enabled:
        return {"enabled": False, "providers": []}
    mgr = get_oauth_manager()
    return {"enabled": True, "providers": mgr.list_providers()}


@router.get("/auth/oauth/login/{provider}", tags=["auth"])
async def oauth_login(provider: str, request: Request) -> RedirectResponse:
    """Initiate OAuth login flow."""
    if not settings.auth_enabled or not settings.oauth_enabled:
        raise HTTPException(status_code=404, detail="OAuth not enabled")
    mgr = get_oauth_manager()
    provider_obj = mgr.get_provider(provider)
    if not provider_obj:
        raise HTTPException(status_code=404, detail="OAuth provider not found")
    base = oauth_base_url(request)
    redirect_uri = f"{base}/api/v2/auth/oauth/callback"
    auth_url, state = mgr.create_authorization_url(provider, redirect_uri)
    response = RedirectResponse(url=auth_url)
    response.set_cookie(
        "oauth_state", state, httponly=True, secure=request.url.scheme == "https",
        samesite="lax", max_age=600, path="/api/v2/auth/oauth/callback",
    )
    return response


@router.get("/auth/oauth/callback", tags=["auth"])
async def oauth_callback(
    request: Request,
    code: str = "",
    state: str = "",
    error: str = "",
) -> RedirectResponse:
    """Handle OAuth callback and hand the API token to Studio through a URL fragment."""
    if not settings.auth_enabled or not settings.oauth_enabled:
        raise HTTPException(status_code=404, detail="OAuth not enabled")
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code or state")

    # Verify state from cookie
    cookie_state = request.cookies.get("oauth_state", "")
    if not cookie_state or cookie_state != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    mgr = get_oauth_manager()
    base = oauth_base_url(request)
    redirect_uri = f"{base}/api/v2/auth/oauth/callback"

    # ป้องกันไม่ให้ login state ถูกใช้กับ callback สำหรับเชื่อมบัญชี
    stored = mgr._state_store.get(state)
    if not stored or stored[3] is not None:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    provider_name = stored[0]

    try:
        result = await mgr.exchange_code_for_provider(provider_name, redirect_uri, code, state)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    userinfo = result["userinfo"]

    # Find or create user
    user = await find_or_create_oauth_user(provider_name, userinfo)
    token = issue_token(user)
    audit("auth.oauth.login", actor=user["username"], provider=provider_name)

    response = RedirectResponse(url=f"{base}/studio#oauth_token={token}", status_code=303)
    response.delete_cookie("oauth_state", path="/api/v2/auth/oauth/callback")
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@router.post("/auth/oauth/link/{provider}", tags=["auth"])
async def oauth_link(
    provider: str,
    request: Request,
    actor: dict[str, str] = Depends(current_actor),
) -> JSONResponse:
    """Link current authenticated user to an OAuth provider."""
    if not settings.auth_enabled or not settings.oauth_enabled:
        raise HTTPException(status_code=404, detail="OAuth not enabled")
    mgr = get_oauth_manager()
    provider_obj = mgr.get_provider(provider)
    if not provider_obj:
        raise HTTPException(status_code=404, detail="OAuth provider not found")
    base = oauth_base_url(request)
    redirect_uri = f"{base}/api/v2/auth/oauth/callback/link"
    auth_url, state = mgr.create_authorization_url(provider, redirect_uri, subject=actor["username"])
    response = JSONResponse({"auth_url": auth_url, "state": state})
    response.set_cookie(
        "oauth_link_state", state, httponly=True, secure=request.url.scheme == "https",
        samesite="lax", max_age=600, path="/api/v2/auth/oauth/callback/link",
    )
    return response


@router.get("/auth/oauth/callback/link", tags=["auth"])
async def oauth_callback_link(
    request: Request,
    code: str = "",
    state: str = "",
    error: str = "",
) -> RedirectResponse:
    """Handle OAuth link callback."""
    if not settings.auth_enabled or not settings.oauth_enabled:
        raise HTTPException(status_code=404, detail="OAuth not enabled")
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code or state")
    if request.cookies.get("oauth_link_state", "") != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    mgr = get_oauth_manager()
    base = oauth_base_url(request)
    redirect_uri = f"{base}/api/v2/auth/oauth/callback/link"

    stored = mgr._state_store.get(state)
    if not stored or not stored[3]:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    provider_name = stored[0]
    username = stored[3]

    try:
        result = await mgr.exchange_code_for_provider(provider_name, redirect_uri, code, state)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    userinfo = result["userinfo"]
    sub = str(userinfo.get("sub") or userinfo.get("id") or "")
    if not sub:
        raise HTTPException(status_code=400, detail="OAuth userinfo missing subject")

    try:
        with connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            user = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
            if user is None:
                raise HTTPException(status_code=401, detail="OAuth link owner no longer exists")
            linked = conn.execute(
                "SELECT user_id FROM oauth_links WHERE provider=? AND provider_sub=?",
                (provider_name, sub),
            ).fetchone()
            if linked and linked["user_id"] != user["id"]:
                raise HTTPException(status_code=409, detail="OAuth identity is already linked to another account")
            conn.execute(
                "INSERT INTO oauth_links(user_id, provider, provider_sub) VALUES(?,?,?) "
                "ON CONFLICT(user_id, provider) DO UPDATE SET provider_sub=excluded.provider_sub",
                (user["id"], provider_name, sub),
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="OAuth identity is already linked to another account") from exc

    audit("auth.oauth.link", actor=username, provider=provider_name)
    response = RedirectResponse(url=f"{base}/studio#oauth_linked=1", status_code=303)
    response.delete_cookie("oauth_link_state", path="/api/v2/auth/oauth/callback/link")
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


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
    try:
        asset_path = validate_managed_asset_path(payload.path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = add_asset(project_id, payload.kind, payload.name, str(asset_path))
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
