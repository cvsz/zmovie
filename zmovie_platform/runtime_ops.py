from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import DB_PATH, connect
from .worker_queue import get as get_worker_job
from .worker_queue import list_jobs as list_worker_jobs
from .worker_queue import queue_status, recover_stale, set_paused

DATA_ROOT = Path(os.getenv("ZMOVIE_DATA_DIR", str(DB_PATH.parent)))
BACKUP_ROOT = Path(os.getenv("ZMOVIE_BACKUP_DIR", "/var/backups/zmovie"))
EVIDENCE_ROOT = Path(os.getenv("ZMOVIE_EVIDENCE_ROOT", str(DATA_ROOT / "evidence")))
BACKUP_RETENTION = max(14, int(os.getenv("ZMOVIE_BACKUP_RETENTION", "14")))


def _json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def _run(argv: list[str], timeout: int = 15) -> dict[str, Any]:
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "ok": False, "detail": type(exc).__name__}
    text = (proc.stdout or proc.stderr or "").strip()
    return {"available": True, "ok": proc.returncode == 0, "returncode": proc.returncode, "output": text[:4000]}


def renderer_doctor() -> dict[str, Any]:
    dri = Path("/dev/dri")
    render_nodes = sorted(str(path) for path in dri.glob("renderD*")) if dri.is_dir() else []
    groups: dict[str, Any] = {}
    for name in ("render", "video"):
        result = _run(["getent", "group", name])
        groups[name] = {"exists": bool(result.get("ok"))}
    return {
        "hostname": socket.gethostname(),
        "dri_exists": dri.is_dir(),
        "render_nodes": [Path(item).name for item in render_nodes],
        "groups": groups,
        "vulkaninfo": _run(["vulkaninfo", "--summary"]),
        "sd_cli_devices": _run([os.getenv("ZMOVIE_SDCPP_BIN", "sd-cli"), "--list-devices"]),
    }


def backup_database() -> dict[str, Any]:
    if not DB_PATH.is_file():
        return {"status": "skipped", "reason": "database_missing", "database": DB_PATH.name}
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = BACKUP_ROOT / f"zmovie-{stamp}.db"
    temp = target.with_suffix(".tmp")
    temp.unlink(missing_ok=True)
    try:
        with sqlite3.connect(DB_PATH) as src, sqlite3.connect(temp) as dst:
            src.backup(dst)
        with sqlite3.connect(temp) as check:
            quick = check.execute("PRAGMA quick_check").fetchone()
            foreign = check.execute("PRAGMA foreign_key_check").fetchall()
        if quick is None or str(quick[0]).lower() != "ok" or foreign:
            raise RuntimeError("backup integrity validation failed")
        temp.replace(target)
        os.chmod(target, 0o640)
    finally:
        temp.unlink(missing_ok=True)
    verified = sorted(BACKUP_ROOT.glob("zmovie-*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in verified[BACKUP_RETENTION:]:
        if old != target:
            old.unlink(missing_ok=True)
    return {"status": "completed", "file": target.name, "retention": BACKUP_RETENTION, "size_bytes": target.stat().st_size}


def backups() -> dict[str, Any]:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    items = sorted(BACKUP_ROOT.glob("zmovie-*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {"count": len(items), "items": [{"name": p.name, "size_bytes": p.stat().st_size} for p in items[:100]]}


def backup_status() -> dict[str, Any]:
    listing = backups()
    newest = listing["items"][0] if listing["items"] else None
    return {"database_exists": DB_PATH.is_file(), "backup_count": listing["count"], "newest": newest, "retention": BACKUP_RETENTION}


def watchdog_status() -> dict[str, Any]:
    disk = shutil.disk_usage(DATA_ROOT if DATA_ROOT.exists() else DB_PATH.parent)
    db_ok = False
    try:
        with connect() as conn:
            db_ok = str(conn.execute("PRAGMA quick_check").fetchone()[0]).lower() == "ok"
    except Exception:
        db_ok = False
    queue = queue_status()
    return {
        "database_ok": db_ok,
        "data_writable": os.access(DATA_ROOT if DATA_ROOT.exists() else DB_PATH.parent, os.W_OK),
        "disk_free_bytes": disk.free,
        "queue": queue,
        "web_service": _run(["systemctl", "is-active", "zmovie"]),
        "worker_service": _run(["systemctl", "is-active", "zmovie-worker"]),
    }


def watchdog_run() -> dict[str, Any]:
    status = watchdog_status()
    actions: list[str] = []
    if not status["database_ok"]:
        actions.append("database_unhealthy")
    if not status["data_writable"]:
        actions.append("data_not_writable")
    if int(status["disk_free_bytes"]) < 512 * 1024 * 1024:
        actions.append("disk_space_critical")
    # Renderer/model readiness intentionally does not trigger restarts.
    return {"healthy": not actions, "actions": actions, "status": status}


def upgrade_readiness() -> dict[str, Any]:
    jobs = list_worker_jobs(limit=1000)
    active = [j for j in jobs if str(j.get("status")) in {"claimed", "running"}]
    ambiguous = [j for j in jobs if str(j.get("status")) == "recovery_required"]
    return {
        "safe": not active and not ambiguous,
        "active_jobs": [{"id": j["id"], "type": j["job_type"], "status": j["status"]} for j in active],
        "recovery_required": [{"id": j["id"], "type": j["job_type"]} for j in ambiguous],
        "policy": "refuse upgrade while active work or ambiguous external state exists",
    }


def sdcpp_evidence(run_smoke: bool = False) -> dict[str, Any]:
    report = renderer_doctor()
    report.update(
        {
            "schema": "zmovie.runtime-evidence/v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "hostname": socket.gethostname(),
            "ffmpeg": _run(["ffmpeg", "-version"]),
            "ffprobe": _run(["ffprobe", "-version"]),
            "model_root_exists": Path("/var/lib/zmovie/models").is_dir(),
            "run_smoke_requested": bool(run_smoke),
            "real_model_verified": False,
        }
    )
    if run_smoke:
        report["smoke"] = {"status": "blocked", "reason": "explicit model-specific smoke is not auto-inferred; configure a video-capable model and invoke the maintained renderer command"}
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-sdcpp-runtime.json")
    target = EVIDENCE_ROOT / name
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    report["evidence_file"] = name
    report["evidence_sha256"] = digest
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="zMovie resilient runtime operations")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("worker-status")
    jobs = sub.add_parser("worker-jobs")
    jobs.add_argument("--limit", type=int, default=100)
    job = sub.add_parser("worker-job")
    job.add_argument("id")
    recover = sub.add_parser("worker-recover")
    recover.add_argument("--apply", action="store_true")
    sub.add_parser("worker-pause")
    sub.add_parser("worker-resume")
    sub.add_parser("renderer-doctor")
    sub.add_parser("vulkan-status")
    sub.add_parser("backup")
    sub.add_parser("backups")
    sub.add_parser("backup-status")
    sub.add_parser("watchdog-status")
    sub.add_parser("watchdog-run")
    sub.add_parser("upgrade-readiness")
    evidence = sub.add_parser("sdcpp-evidence")
    evidence.add_argument("--run-smoke", action="store_true")
    args = parser.parse_args()

    command = args.command
    if command == "worker-status":
        _json(queue_status())
    elif command == "worker-jobs":
        _json(list_worker_jobs(limit=args.limit))
    elif command == "worker-job":
        item = get_worker_job(args.id)
        if item is None:
            raise SystemExit("worker job not found")
        _json(item)
    elif command == "worker-recover":
        _json({"apply": bool(args.apply), "stale": recover_stale(apply=args.apply)})
    elif command == "worker-pause":
        set_paused(True)
        _json({"paused": True})
    elif command == "worker-resume":
        set_paused(False)
        _json({"paused": False})
    elif command in {"renderer-doctor", "vulkan-status"}:
        _json(renderer_doctor())
    elif command == "backup":
        _json(backup_database())
    elif command == "backups":
        _json(backups())
    elif command == "backup-status":
        _json(backup_status())
    elif command == "watchdog-status":
        _json(watchdog_status())
    elif command == "watchdog-run":
        report = watchdog_run()
        _json(report)
        return 0 if report["healthy"] else 1
    elif command == "upgrade-readiness":
        report = upgrade_readiness()
        _json(report)
        return 0 if report["safe"] else 2
    elif command == "sdcpp-evidence":
        _json(sdcpp_evidence(run_smoke=args.run_smoke))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
