from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from .api_routes import current_actor, require_project
from .audit import write as audit
from .auth import (
    MEDIA_PREVIEW_TOKEN_TTL_SECONDS,
    decode_media_preview_token,
    issue_media_preview_token,
)
from .repository import list_assets

router = APIRouter(prefix="/api/v2")


def _media_root() -> Path:
    return Path(os.getenv("ZMOVIE_MEDIA_ROOT", "data/media")).expanduser().resolve()


def _asset_for_preview(project_id: str, asset_id: str) -> tuple[dict[str, Any], Path]:
    asset = next((item for item in list_assets(project_id) if str(item.get("id")) == asset_id), None)
    if asset is None:
        raise HTTPException(status_code=404, detail="asset not found")

    raw_path = str(asset.get("path") or "").strip()
    if not raw_path:
        raise HTTPException(status_code=404, detail="asset has no media path")
    path = Path(raw_path).expanduser().resolve()
    if path.suffix.lower() != ".mp4":
        raise HTTPException(status_code=415, detail="Studio preview currently supports MP4 assets only")

    root = _media_root()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="asset is outside the managed media root") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="asset media file not found")
    return asset, path


@router.post("/projects/{project_id}/assets/{asset_id}/preview", tags=["assets"])
def create_preview_url(
    project_id: str,
    asset_id: str,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    require_project(project_id, actor)
    asset, _ = _asset_for_preview(project_id, asset_id)
    preview_token = issue_media_preview_token(
        project_id=project_id,
        asset_id=asset_id,
        subject=actor["username"],
    )
    audit(
        "asset.preview.issue",
        actor=actor["username"],
        project_id=project_id,
        asset_id=asset_id,
    )
    return {
        "asset_id": asset_id,
        "kind": asset.get("kind", ""),
        "name": asset.get("name", ""),
        "url": f"/api/v2/media/previews/{preview_token}",
        "expires_in": MEDIA_PREVIEW_TOKEN_TTL_SECONDS,
    }


@router.get("/media/previews/{preview_token}", tags=["assets"], include_in_schema=False)
def stream_preview(preview_token: str) -> FileResponse:
    payload = decode_media_preview_token(preview_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="invalid or expired media preview token")
    project_id = str(payload["project_id"])
    asset_id = str(payload["asset_id"])
    asset, path = _asset_for_preview(project_id, asset_id)
    response = FileResponse(
        path=path,
        media_type="video/mp4",
        headers={
            "Cache-Control": "private, no-store",
            "Content-Disposition": "inline",
            "X-zMovie-Asset-ID": str(asset.get("id") or ""),
        },
    )
    return response
