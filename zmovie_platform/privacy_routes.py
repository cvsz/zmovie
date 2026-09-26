"""Privacy API: export my data, delete my account (explicit confirmation)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .api_routes import current_actor
from .privacy import delete_user_data, export_user_data

router = APIRouter(prefix="/api/v2")


class DeleteRequest(BaseModel):
    confirmation: str = Field(min_length=3, max_length=100)


@router.get("/privacy/export", tags=["privacy"])
def privacy_export(actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    try:
        return {"export": export_user_data(str(actor.get("username", "")))}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/privacy/delete", tags=["privacy"])
def privacy_delete(payload: DeleteRequest, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    try:
        return delete_user_data(str(actor.get("username", "")), confirmation=payload.confirmation)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
