#!/usr/bin/env python3
"""zMovie full-stack API server."""

from __future__ import annotations

import json
import os
import random
import sqlite3
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import zmovie
from zmovie_platform.auth import decode_token
from zmovie_platform.config import settings
from zmovie_platform.rate_limit import allowed

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
# Keep the legacy prompt/history API on the exact same writable database path as
# the production v2 platform. Native systemd deployments set ZMOVIE_DB_PATH to
# /var/lib/zmovie/zmovie.db while ProtectSystem=strict makes /opt/zmovie read-only.
# Deriving DATA_DIR from DB_PATH prevents startup from attempting to create
# /opt/zmovie/data and also avoids maintaining two independent SQLite files.
_default_data_dir = Path(os.getenv("ZMOVIE_DATA_DIR", str(BASE_DIR / "data"))).expanduser()
DB_PATH = Path(os.getenv("ZMOVIE_DB_PATH", str(_default_data_dir / "zmovie.db"))).expanduser().resolve()
DATA_DIR = DB_PATH.parent
APP_VERSION = "0.2.1"


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() not in {"0", "false", "no", "off"}


DOCS_ENABLED = _env_flag("ZMOVIE_ENABLE_DOCS")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title="zMovie Prompt Generator",
    version=APP_VERSION,
    description="Full-stack cinematic prompt generator API backed by the zMovie core engine.",
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class GenerateRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=100)
    seed: int | None = None
    save_history: bool = True


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                seed INTEGER,
                title TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_generation(item: dict[str, Any], seed: int | None) -> int:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO generations (created_at, seed, title, payload) VALUES (?, ?, ?, ?)",
            (now, seed, str(item["title"]), json.dumps(item, ensure_ascii=False)),
        )
        conn.commit()
        return int(cursor.lastrowid)


@app.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    """Keep the legacy URL but send operators to the authenticated Studio."""
    return RedirectResponse("/studio", status_code=307)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "zmovie",
        "version": APP_VERSION,
        "database_exists": DB_PATH.exists(),
    }


@app.get("/api/options")
def options() -> dict[str, Any]:
    return {
        "settings": zmovie.SETTINGS,
        "times": zmovie.TIMES,
        "faces": zmovie.FACES,
        "hair": zmovie.HAIR,
        "outfits": zmovie.OUTFITS,
        "personalities": zmovie.PERSONALITIES,
        "attackers": zmovie.ATTACKERS,
        "attacker_styles": zmovie.ATTACKER_STYLES,
        "lead_styles": zmovie.LEAD_STYLES,
        "destruction": zmovie.DESTRUCTION,
        "endings": zmovie.ENDINGS,
        "cameras": zmovie.CAMERAS,
        "lighting": zmovie.LIGHTING,
        "visual_styles": zmovie.VISUAL_STYLES,
        "finishers": zmovie.FINISHERS,
    }


def legacy_admin(authorization: str | None = Header(default=None)) -> dict[str, str]:
    if not settings.auth_enabled:
        return {"username": "local", "role": "admin"}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(authorization.split(" ", 1)[1].strip())
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    return {"username": str(payload.get("sub", "admin")), "role": "admin"}


def legacy_generate_rate_limit(request: Request) -> None:
    host = request.client.host if request.client else "unknown"
    if not allowed(f"legacy-generate:{host}", limit=30, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="generation rate limit exceeded",
            headers={"Retry-After": "60"},
        )


@app.post("/api/generate", dependencies=[Depends(legacy_admin), Depends(legacy_generate_rate_limit)])
def generate(request: GenerateRequest) -> dict[str, Any]:
    rng = random.Random(request.seed)
    results: list[dict[str, Any]] = []

    for _ in range(request.count):
        item = zmovie.generate(rng)
        if request.save_history:
            item = dict(item)
            item["history_id"] = save_generation(item, request.seed)
        results.append(item)

    return {
        "seed": request.seed,
        "count": len(results),
        "results": results,
    }


@app.get("/api/history", dependencies=[Depends(legacy_admin)])
def history(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, created_at, seed, title, payload FROM generations ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()

    items = []
    for row in rows:
        payload = json.loads(row["payload"])
        items.append(
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "seed": row["seed"],
                "title": row["title"],
                "payload": payload,
            }
        )
    return {"count": len(items), "items": items}


@app.get("/api/history/{generation_id}", dependencies=[Depends(legacy_admin)])
def history_item(generation_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, created_at, seed, title, payload FROM generations WHERE id = ?",
            (generation_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Generation not found")

    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "seed": row["seed"],
        "title": row["title"],
        "payload": json.loads(row["payload"]),
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("ZMOVIE_HOST", "0.0.0.0")
    port = int(os.getenv("ZMOVIE_PORT", "8080"))
    uvicorn.run("main:app", host=host, port=port, reload=False)
