from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import Any

from .exporter import export_project
from .media import assemble_project, probe_media
from .models import utcnow
from .pipeline import render_project
from .providers import provider_specs
from .qc import inspect_project
from .repository import add_asset, get_project, list_assets, list_jobs
from .security import validate_managed_asset_path
from .publishers.bilibili_hardened import list_publish_jobs, prepare_bilibili_publish

EXPORT_ROOT = Path(os.getenv("ZMOVIE_EXPORT_ROOT", "data/exports"))
PUBLISH_ROOT = Path(os.getenv("ZMOVIE_PUBLISH_ROOT", "data/publish"))
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}


def _valid_project_id(project_id: str) -> str:
    value = str(project_id or "").strip()
    if not value or not value.replace("_", "").isalnum():
        raise ValueError("invalid project id")
    return value


def production_video_report(raw_path: str) -> dict[str, Any]:
    report: dict[str, Any] = {"ready": False, "path": str(raw_path or ""), "reason": "unknown"}
    try:
        path = validate_managed_asset_path(str(raw_path or ""))
    except ValueError:
        report["reason"] = "path_not_managed"
        return report
    if not path.is_file():
        report["reason"] = "file_missing"
        return report
    if path.suffix.lower() not in VIDEO_EXTENSIONS:
        report["reason"] = "not_video_file"
        return report
    info = probe_media(str(path))
    probe = info.get("probe")
    if not isinstance(probe, dict):
        report["reason"] = "ffprobe_required_or_probe_failed"
        return report
    streams = probe.get("streams") or []
    video = next((item for item in streams if isinstance(item, dict) and item.get("codec_type") == "video"), None)
    if not isinstance(video, dict):
        report["reason"] = "video_stream_missing"
        return report
    duration_raw = (probe.get("format") or {}).get("duration") or video.get("duration") or 0
    try:
        duration = float(duration_raw)
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 0:
        report["reason"] = "duration_invalid"
        return report
    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    if width <= 0 or height <= 0:
        report["reason"] = "dimensions_invalid"
        return report
    report.update(
        {
            "ready": True,
            "reason": "ok",
            "path": str(path),
            "size_bytes": int(info.get("size_bytes") or path.stat().st_size),
            "codec": str(video.get("codec_name") or ""),
            "width": width,
            "height": height,
            "duration_seconds": duration,
        }
    )
    return report


def _production_providers() -> list[dict[str, Any]]:
    return [
        item
        for item in provider_specs()
        if item.get("id") != "mock" and bool(item.get("configured"))
    ]


def _shot_video_map(project_id: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    project = get_project(project_id)
    if project is None:
        raise ValueError("project not found")
    expected = [shot.id for scene in project.scenes for shot in scene.shots]
    selected: dict[str, dict[str, Any]] = {}
    for job in list_jobs(project_id, limit=5000):
        shot_id = str(job.get("shot_id") or "")
        if shot_id not in expected or shot_id in selected:
            continue
        if str(job.get("status")) != "completed" or not job.get("output_path"):
            continue
        media = production_video_report(str(job["output_path"]))
        if media["ready"]:
            selected[shot_id] = {"job": job, "media": media}
    missing = [shot_id for shot_id in expected if shot_id not in selected]
    return selected, missing


def _final_video(project_id: str) -> dict[str, Any] | None:
    for asset in list_assets(project_id, "final"):
        raw = str(asset.get("path") or "")
        if not raw:
            continue
        media = production_video_report(raw)
        if media["ready"]:
            return {"asset": asset, "media": media}
    return None


def production_readiness(project_id: str) -> dict[str, Any]:
    project_id = _valid_project_id(project_id)
    project = get_project(project_id)
    if project is None:
        raise ValueError("project not found")
    qc = inspect_project(project)
    shot_map, missing = _shot_video_map(project_id)
    total_shots = sum(len(scene.shots) for scene in project.scenes)
    final = _final_video(project_id)
    providers = _production_providers()
    export_path = EXPORT_ROOT / f"{project_id}.zip"
    return {
        "schema": "zmovie.production-readiness/v1",
        "project_id": project_id,
        "qc": {
            "passed": bool(qc.get("passed")),
            "score": int(qc.get("score") or 0),
            "errors": int(qc.get("errors") or 0),
            "warnings": int(qc.get("warnings") or 0),
        },
        "render": {
            "ready": total_shots > 0 and not missing,
            "completed_shots": len(shot_map),
            "total_shots": total_shots,
            "missing_shots": missing,
        },
        "assemble": {"ready": bool(qc.get("passed")) and total_shots > 0 and not missing},
        "final": {
            "ready": final is not None,
            "asset_id": str((final or {}).get("asset", {}).get("id") or ""),
            "codec": str((final or {}).get("media", {}).get("codec") or ""),
            "width": int((final or {}).get("media", {}).get("width") or 0),
            "height": int((final or {}).get("media", {}).get("height") or 0),
            "duration_seconds": float((final or {}).get("media", {}).get("duration_seconds") or 0),
        },
        "bilibili_prepare": {"ready": final is not None},
        "export": {"ready": final is not None, "package_exists": export_path.is_file()},
        "providers": [
            {"id": str(item.get("id") or ""), "name": str(item.get("name") or "")}
            for item in providers
        ],
    }


def _require_production_provider(provider_id: str) -> None:
    provider_id = str(provider_id or "").strip()
    if provider_id == "mock":
        raise RuntimeError("Local mock is a dry-run provider and cannot be used for production rendering")
    available = {str(item.get("id")) for item in _production_providers()}
    if provider_id not in available:
        raise RuntimeError(f"production render provider is not configured: {provider_id}")


def render_all_production(project_id: str, provider_id: str, max_workers: int = 2) -> dict[str, Any]:
    _require_production_provider(provider_id)
    project = get_project(project_id)
    if project is None:
        raise ValueError("project not found")
    qc = inspect_project(project)
    if not qc.get("passed"):
        return {"status": "blocked", "reason": "quality-control", "qc": qc}
    result = render_project(project_id, provider_id, max_workers)
    readiness = production_readiness(project_id)
    if not readiness["render"]["ready"]:
        return {
            "status": "failed",
            "reason": "production-media-validation",
            "render": result,
            "readiness": readiness,
        }
    return {"status": "completed", "render": result, "readiness": readiness}


def assemble_production(project_id: str) -> dict[str, Any]:
    project_id = _valid_project_id(project_id)
    project = get_project(project_id)
    if project is None:
        raise ValueError("project not found")
    shot_map, missing = _shot_video_map(project_id)
    if missing:
        raise RuntimeError(f"production assembly requires a valid completed video for every shot; missing={len(missing)}")
    clips = [
        str(shot_map[shot.id]["media"]["path"])
        for scene in project.scenes
        for shot in scene.shots
    ]
    result = assemble_project(project, clips)
    if str(result.get("status")) != "completed":
        raise RuntimeError(f"production assembly did not create final video: {result.get('status')}")
    media = production_video_report(str(result.get("output_path") or ""))
    if not media["ready"]:
        raise RuntimeError(f"assembled final failed production media validation: {media['reason']}")

    output = Path(str(media["path"])).resolve()
    existing = next(
        (
            asset
            for asset in list_assets(project_id, "final")
            if str(asset.get("path") or "") and Path(str(asset["path"])).expanduser().resolve() == output
        ),
        None,
    )
    asset = existing or add_asset(
        project_id,
        "final",
        "production assembled movie",
        str(output),
        {
            "production": True,
            "codec": media["codec"],
            "width": media["width"],
            "height": media["height"],
            "duration_seconds": media["duration_seconds"],
            "clip_count": len(clips),
        },
    )
    return {
        "status": "completed",
        "project_id": project_id,
        "clip_count": len(clips),
        "asset_id": str(asset.get("id") or ""),
        "media": {key: media[key] for key in ("codec", "width", "height", "duration_seconds", "size_bytes")},
    }


def prepare_bilibili_production(
    project_id: str,
    *,
    title: str = "",
    description: str = "",
    tags: list[str] | None = None,
    playlist: str = "",
    content_type: str = "Original",
    schedule_at: str = "",
) -> dict[str, Any]:
    project_id = _valid_project_id(project_id)
    final = _final_video(project_id)
    if final is None:
        raise RuntimeError("production Bilibili package requires an assembled, ffprobe-validated final video")
    job = prepare_bilibili_publish(
        project_id,
        title=title,
        description=description,
        tags=tags,
        playlist=playlist,
        content_type=content_type,
        schedule_at=schedule_at,
    )
    selected = Path(str(job.get("video_path") or "")).expanduser().resolve()
    expected = Path(str(final["media"]["path"])).expanduser().resolve()
    if selected != expected:
        raise RuntimeError("Bilibili package did not bind to the validated production final asset")
    return job


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_managed_file(raw_path: str, target: Path) -> Path:
    source = validate_managed_asset_path(raw_path)
    if not source.is_file():
        raise FileNotFoundError(f"managed package source does not exist: {source.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def export_production_package(project_id: str) -> Path:
    project_id = _valid_project_id(project_id)
    project = get_project(project_id)
    if project is None:
        raise ValueError("project not found")
    final = _final_video(project_id)
    if final is None:
        raise RuntimeError("production export requires an assembled, ffprobe-validated final video")

    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    package_dir = EXPORT_ROOT / project_id
    archive = EXPORT_ROOT / f"{project_id}.zip"
    if package_dir.exists():
        shutil.rmtree(package_dir)
    if archive.exists():
        archive.unlink()

    # Build the portable metadata/prompt package first, then add production media.
    export_project(project, EXPORT_ROOT)
    final_source = Path(str(final["media"]["path"]))
    final_target = package_dir / "media" / ("final" + final_source.suffix.lower())
    _copy_managed_file(str(final_source), final_target)

    publish_summary: dict[str, Any] = {}
    jobs = list_publish_jobs(project_id=project_id, limit=1)
    if jobs:
        job = jobs[0]
        publish_summary = {
            key: job.get(key)
            for key in (
                "id",
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
        }
        publish_dir = package_dir / "publish"
        publish_dir.mkdir(parents=True, exist_ok=True)
        (publish_dir / "job.json").write_text(json.dumps(publish_summary, ensure_ascii=False, indent=2), encoding="utf-8")
        cover_path = str(job.get("cover_path") or "")
        if cover_path:
            try:
                source = validate_managed_asset_path(cover_path)
                if source.is_file():
                    _copy_managed_file(str(source), publish_dir / ("cover" + source.suffix.lower()))
            except ValueError:
                pass
        manifest = PUBLISH_ROOT / project_id / str(job.get("id") or "") / "publication.json"
        try:
            manifest = validate_managed_asset_path(str(manifest))
        except ValueError:
            manifest = Path()
        if manifest.is_file():
            _copy_managed_file(str(manifest), publish_dir / "publication.json")

    package_meta = {
        "schema": "zmovie.production-package/v1",
        "project_id": project_id,
        "generated_at": utcnow(),
        "final": {
            "file": final_target.relative_to(package_dir).as_posix(),
            "codec": final["media"]["codec"],
            "width": final["media"]["width"],
            "height": final["media"]["height"],
            "duration_seconds": final["media"]["duration_seconds"],
        },
        "bilibili_job": publish_summary.get("id", ""),
        "bilibili_status": publish_summary.get("status", ""),
    }
    (package_dir / "package.json").write_text(json.dumps(package_meta, ensure_ascii=False, indent=2), encoding="utf-8")

    package_files = sorted(path for path in package_dir.rglob("*") if path.is_file() and path.name != "checksums.sha256")
    checksum_lines = [f"{_sha256(path)}  {path.relative_to(package_dir).as_posix()}" for path in package_files]
    (package_dir / "checksums.sha256").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        for path in sorted(item for item in package_dir.rglob("*") if item.is_file()):
            handle.write(path, path.relative_to(package_dir))
    return archive


def _run_path(project_id: str, run_id: str) -> Path:
    project_id = _valid_project_id(project_id)
    run_id = str(run_id or "").strip()
    if not run_id or not run_id.replace("_", "").isalnum():
        raise ValueError("invalid production run id")
    return EXPORT_ROOT / "production-runs" / project_id / f"{run_id}.json"


def _write_run(payload: dict[str, Any]) -> dict[str, Any]:
    target = _run_path(str(payload["project_id"]), str(payload["id"]))
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(target)
    return payload


def get_production_run(project_id: str, run_id: str) -> dict[str, Any] | None:
    target = _run_path(project_id, run_id)
    if not target.is_file():
        return None
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def latest_production_run(project_id: str) -> dict[str, Any] | None:
    root = EXPORT_ROOT / "production-runs" / _valid_project_id(project_id)
    if not root.is_dir():
        return None
    files = sorted(root.glob("prod_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    for path in files:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            return value
    return None


def start_production_run(project_id: str, provider_id: str, max_workers: int, bilibili: dict[str, Any]) -> dict[str, Any]:
    _valid_project_id(project_id)
    _require_production_provider(provider_id)
    current = latest_production_run(project_id)
    if current and current.get("status") in {"queued", "running"}:
        raise RuntimeError(f"production run already active: {current.get('id')}")
    run = {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "project_id": project_id,
        "provider": provider_id,
        "max_workers": max(1, min(int(max_workers), 8)),
        "status": "queued",
        "stage": "queued",
        "bilibili": dict(bilibili),
        "publish_job_id": "",
        "error": "",
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    return _write_run(run)


def execute_production_run(project_id: str, run_id: str) -> dict[str, Any]:
    run = get_production_run(project_id, run_id)
    if run is None:
        raise ValueError("production run not found")

    def update(**fields: Any) -> None:
        run.update(fields)
        run["updated_at"] = utcnow()
        _write_run(run)

    try:
        update(status="running", stage="render", error="")
        render = render_all_production(project_id, str(run["provider"]), int(run["max_workers"]))
        if render.get("status") != "completed":
            raise RuntimeError(f"production render did not complete: {render.get('reason') or render.get('status')}")
        update(stage="assemble")
        assemble_production(project_id)
        update(stage="prepare-bilibili")
        bili = dict(run.get("bilibili") or {})
        job = prepare_bilibili_production(
            project_id,
            title=str(bili.get("title") or ""),
            description=str(bili.get("description") or ""),
            tags=list(bili.get("tags") or []) or None,
            playlist=str(bili.get("playlist") or ""),
            content_type=str(bili.get("content_type") or "Original"),
            schedule_at=str(bili.get("schedule_at") or ""),
        )
        update(stage="export", publish_job_id=str(job.get("id") or ""))
        export_production_package(project_id)
        update(status="completed", stage="approval-gate")
    except Exception as exc:
        update(status="failed", stage="failed", error=str(exc)[:1000])
    return run
