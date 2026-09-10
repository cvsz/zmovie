from __future__ import annotations

from pathlib import Path

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app import app
from zmovie_platform.api_routes import router as v2_router
from zmovie_platform.config import settings
from zmovie_platform.logging_config import configure_logging
from zmovie_platform.media_preview import router as media_preview_router
from zmovie_platform.migrations import migrate
from zmovie_platform.product_routes import router as product_router
from zmovie_platform.production_routes import router as production_router
from zmovie_platform.publisher_routes import router as publisher_router
from zmovie_platform.security import SECURITY_HEADERS

configure_logging()
migrate()
app.include_router(v2_router)
app.include_router(media_preview_router)
app.include_router(publisher_router)
app.include_router(production_router)
app.include_router(product_router)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )


@app.middleware("http")
async def production_security_headers(request: Request, call_next):
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    response.headers.setdefault("Cache-Control", "no-store" if request.url.path.startswith("/api/") else "public, max-age=300")
    return response


@app.get("/studio", include_in_schema=False)
def studio() -> HTMLResponse:
    html = Path("static/studio.html").read_text(encoding="utf-8")
    hooks = (
        '<script src="/static/studio-preview.js"></script>',
        '<script src="/static/hyperframes-studio.js"></script>',
        '<script src="/static/durable-worker.js"></script>',
    )
    for hook in hooks:
        if hook not in html:
            html = html.replace("</body>", hook + "\n</body>")
    return HTMLResponse(html)


@app.get("/product", include_in_schema=False)
def product_studio() -> HTMLResponse:
    return HTMLResponse(Path("static/product.html").read_text(encoding="utf-8"))
