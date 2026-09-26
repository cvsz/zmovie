"""Authenticated media upload boundary (validated, quota-checked)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from . import media_pipeline
from .api_routes import current_actor, require_project
from .audit import write as audit
from .repository import add_asset

router = APIRouter(prefix="/api/v2")

CHUNK = 1024 * 1024


@router.post("/projects/{project_id}/uploads", tags=["media"])
async def upload_media(
    project_id: str,
    file: UploadFile = File(...),
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    project = require_project(project_id, actor)
    filename = file.filename or "upload.bin"
    content_type = file.content_type or ""
    # Stream with an enforced cap (never buffer unbounded input).
    limit = media_pipeline.max_upload_bytes() + 1
    chunks: list[bytes] = []
    total = 0
    while True:
        piece = await file.read(CHUNK)
        if not piece:
            break
        total += len(piece)
        if total > limit:
            audit("media.upload.rejected", actor=str(actor.get("username", "unknown")))
            raise HTTPException(status_code=413, detail="upload exceeds size limit")
        chunks.append(piece)
    content = b"".join(chunks)
    try:
        path = media_pipeline.store_upload(
            project_id=project.id, filename=filename, content=content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    asset = add_asset(project.id, kind="upload", name=path.name, path=str(path),
                      metadata={"size_bytes": len(content), "content_type": content_type})
    audit("media.upload", actor=str(actor.get("username", "unknown")))
    return {"asset": asset, "path": str(path)}
