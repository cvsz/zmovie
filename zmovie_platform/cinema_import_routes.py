"""Cinema import API boundary (explicit human approval, service auth)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from . import studio_cinema
from .api_routes import current_actor, require_project
from .audit import write as audit

router = APIRouter(prefix="/api/v2")


def _service_actor(service_token: str | None = Header(default=None, alias="X-Cinema-Service-Token")) -> str:
    if not studio_cinema.verify_service_token(service_token):
        raise HTTPException(status_code=401, detail="invalid cinema service token")
    return "cinema-service"


def _require_admin(actor: dict[str, str]) -> dict[str, str]:
    if actor.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin approval required")
    return actor


class ImportRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=200)
    production_run_id: str = Field(default="", max_length=200)
    media_path: str = Field(min_length=1, max_length=2000)
    idempotency_key: str = Field(min_length=8, max_length=128)


class RightsRequest(BaseModel):
    rights_holder: str = Field(min_length=1, max_length=200)
    license_expires: str = Field(min_length=4, max_length=40)
    age_rating: str = Field(min_length=1, max_length=20)


class ApproveRequest(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    reason: str = Field(default="", max_length=2000)


class EditorialRequest(BaseModel):
    publish: bool
    cinema_film_ref: str = Field(default="", max_length=500)
    note: str = Field(default="", max_length=2000)


@router.post("/cinema/imports", tags=["cinema"])
def create_import(
    payload: ImportRequest,
    actor: dict[str, str] = Depends(current_actor),
    service: str = Depends(_service_actor),
) -> dict[str, object]:
    require_project(payload.project_id, actor)
    try:
        record = studio_cinema.request_import(
            project_id=payload.project_id,
            production_run_id=payload.production_run_id,
            media_path=payload.media_path,
            idempotency_key=payload.idempotency_key,
            actor=f"{actor.get('username', 'unknown')}+{service}",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"import": record}


@router.get("/cinema/imports", tags=["cinema"])
def cinema_imports(
    project_id: str | None = None,
    status: str | None = None,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    items = studio_cinema.list_imports(project_id=project_id, status=status)
    if actor.get("role") == "admin" or not project_id:
        visible = items
    else:
        try:
            require_project(str(project_id), actor)
            visible = items
        except HTTPException:
            visible = []
    return {"items": visible}


@router.get("/cinema/imports/{import_id}", tags=["cinema"])
def cinema_import(import_id: str, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    record = studio_cinema.get_import(import_id)
    if record is None:
        raise HTTPException(status_code=404, detail="import not found")
    require_project(str(record["project_id"]), actor)
    return {"import": record}


@router.post("/cinema/imports/{import_id}/rights", tags=["cinema"])
def cinema_rights(import_id: str, payload: RightsRequest, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    record = studio_cinema.get_import(import_id)
    if record is None:
        raise HTTPException(status_code=404, detail="import not found")
    require_project(str(record["project_id"]), actor)
    try:
        updated = studio_cinema.confirm_rights(
            import_id=import_id,
            actor=str(actor.get("username", "unknown")),
            confirmation={"owner_verified": True, **payload.model_dump()},
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    audit("cinema.import.rights", actor=str(actor.get("username", "unknown")))
    return {"import": updated}


@router.post("/cinema/imports/{import_id}/approve", tags=["cinema"])
def cinema_approve(import_id: str, payload: ApproveRequest, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    _require_admin(actor)
    try:
        updated = studio_cinema.approve_import(
            import_id=import_id, actor=str(actor.get("username", "unknown")), decision=payload.decision, reason=payload.reason
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"import": updated}


@router.post("/cinema/imports/{import_id}/run", tags=["cinema"])
def cinema_run(
    import_id: str,
    actor: dict[str, str] = Depends(current_actor),
    service: str = Depends(_service_actor),
) -> dict[str, object]:
    record = studio_cinema.get_import(import_id)
    if record is None:
        raise HTTPException(status_code=404, detail="import not found")
    require_project(str(record["project_id"]), actor)
    try:
        updated = studio_cinema.run_import(import_id=import_id, actor=f"{actor.get('username', 'unknown')}+{service}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"import": updated}


@router.post("/cinema/imports/{import_id}/editorial", tags=["cinema"])
def cinema_editorial(import_id: str, payload: EditorialRequest, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    _require_admin(actor)
    try:
        updated = studio_cinema.editorial_decide(
            import_id=import_id,
            actor=str(actor.get("username", "unknown")),
            publish=payload.publish,
            cinema_film_ref=payload.cinema_film_ref,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"import": updated}
