"""Studio-to-Cinema integration boundary.

Explicit pipeline (no auto-publish):

    Studio render
      -> media quality checks (QC hook)
      -> ownership/rights confirmation (human)
      -> human publication approval (admin)
      -> Cinema import (service)
      -> transcoding and poster generation (hooks)
      -> editorial review (admin)
      -> published Cinema film

Only managed filesystem paths are accepted (SSRF/path-traversal safe).
Every transition is recorded in history and in the audit log.
Idempotency keys prevent duplicate imports.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import write as audit_write
from .models import utcnow
from .security import validate_managed_asset_path
from .storage import connect

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cinema_imports (
  id TEXT PRIMARY KEY,
  idempotency_key TEXT UNIQUE NOT NULL,
  project_id TEXT NOT NULL,
  production_run_id TEXT NOT NULL DEFAULT '',
  media_path TEXT NOT NULL,
  status TEXT NOT NULL,
  rights_confirmed INTEGER NOT NULL DEFAULT 0,
  approver TEXT NOT NULL DEFAULT '',
  decision_reason TEXT NOT NULL DEFAULT '',
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT NOT NULL DEFAULT '',
  cinema_film_ref TEXT NOT NULL DEFAULT '',
  history_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cinema_imports_project ON cinema_imports(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_cinema_imports_status ON cinema_imports(status, updated_at);
"""

# สถานะไปข้างหน้าอย่างเดียว ยกเว้น FAILED ที่ retry ได้จาก APPROVED
TERMINAL_STATES = {"published", "rejected"}
APPROVAL_PENDING = "approval_pending"


def ensure_tables() -> None:
    """สร้างตารางแบบ idempotent (เรียกซ้ำได้อย่างปลอดภัย)."""
    with connect() as conn:
        conn.executescript(TABLE_SQL)


def _now() -> str:
    return utcnow()


def service_token_configured() -> bool:
    return bool(os.getenv("ZMOVIE_CINEMA_SERVICE_TOKEN", "").strip())


def verify_service_token(provided: str | None) -> bool:
    """ตรวจ service token แบบ fail-closed (ไม่มี token = ปฏิเสธเสมอ)."""
    expected = os.getenv("ZMOVIE_CINEMA_SERVICE_TOKEN", "")
    if not expected or not provided:
        return False
    return hmac.compare_digest(provided, expected)


def _history(rows: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(rows or "[]")
        return data if isinstance(data, list) else []
    except (ValueError, TypeError):
        return []


def _record(conn: Any, import_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM cinema_imports WHERE id=?", (import_id,)).fetchone()
    return dict(row) if row else None


def _append_history(conn: Any, import_id: str, actor: str, from_status: str, to_status: str, note: str = "") -> None:
    row = _record(conn, import_id)
    history = _history(row["history_json"]) if row else []
    history.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "from": from_status,
            "to": to_status,
            "note": note,
        }
    )
    conn.execute(
        "UPDATE cinema_imports SET status=?, updated_at=?, history_json=? WHERE id=?",
        (to_status, _now(), json.dumps(history, ensure_ascii=False), import_id),
    )
    audit_write("cinema.import.transition", actor=actor, import_id=import_id, from_status=from_status, to_status=to_status, note=note)


def _new_id(idempotency_key: str) -> str:
    digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
    return f"ci_{digest[:24]}"


def default_qc_hook(media_path: str) -> dict[str, Any]:
    """QC เริ่มต้น: ไฟล์ต้องมีอยู่จริงและนามสกุลวิดีโอที่รองรับ."""
    target = Path(media_path)
    if not target.exists() or not target.is_file():
        return {"passed": False, "reason": "media file not found"}
    if target.suffix.lower() not in {".mp4", ".mov", ".mkv", ".webm"}:
        return {"passed": False, "reason": "unsupported container"}
    if target.stat().st_size <= 0:
        return {"passed": False, "reason": "empty media file"}
    return {"passed": True, "size_bytes": target.stat().st_size}


def request_import(
    *,
    project_id: str,
    production_run_id: str,
    media_path: str,
    idempotency_key: str,
    actor: str,
    qc_hook: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """รับงาน import ใหม่ (ไม่เคย publish อัตโนมัติ).

    คืน record เดิมถ้า idempotency_key ซ้ำ (กัน import ซ้ำ).
    """
    ensure_tables()
    key = (idempotency_key or "").strip()
    if len(key) < 8 or len(key) > 128:
        raise ValueError("idempotency_key must be 8-128 characters")
    if not (project_id or "").strip():
        raise ValueError("project_id is required")
    # ตรวจ path ให้อยู่ใต้ managed root ก่อนแตะ filesystem
    resolved = validate_managed_asset_path(media_path)
    if not resolved.exists():
        raise ValueError("media file not found")

    hook = qc_hook or default_qc_hook
    qc = hook(str(resolved))
    if not isinstance(qc, dict) or not qc.get("passed"):
        reason = str(qc.get("reason", "qc failed")) if isinstance(qc, dict) else "qc failed"
        with connect() as conn:
            existing = conn.execute("SELECT * FROM cinema_imports WHERE idempotency_key=?", (key,)).fetchone()
            if existing:
                return dict(existing)
            import_id = _new_id(key)
            now = _now()
            conn.execute(
                "INSERT INTO cinema_imports(id,idempotency_key,project_id,production_run_id,media_path,status,last_error,created_at,updated_at)"
                " VALUES(?,?,?,?,?,?,?, ?, ?) ON CONFLICT(id) DO NOTHING",
                (import_id, key, project_id.strip(), (production_run_id or "").strip(), str(resolved), "qc_failed", reason[:2000], now, now),
            )
            row = _record(conn, import_id)
            if row is None:
                row = dict(conn.execute("SELECT * FROM cinema_imports WHERE idempotency_key=?", (key,)).fetchone())
            _append_history(conn, row["id"], actor, "requested", "qc_failed", reason[:500])
            audit_write("cinema.import.qc_failed", actor=actor, import_id=row["id"], reason=reason[:500])
            return _record(conn, row["id"]) or row
        raise ValueError(f"media QC failed: {reason}")

    with connect() as conn:
        existing = conn.execute("SELECT * FROM cinema_imports WHERE idempotency_key=?", (key,)).fetchone()
        if existing:
            # กัน import ซ้ำ: คืน record เดิม ไม่สร้างใหม่
            return dict(existing)
        import_id = _new_id(key)
        now = _now()
        conn.execute(
            "INSERT INTO cinema_imports(id,idempotency_key,project_id,production_run_id,media_path,status,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING",
            (import_id, key, project_id.strip(), (production_run_id or "").strip(), str(resolved), "qc_passed", now, now),
        )
        row = _record(conn, import_id)
        if row is None:  # แข่งกัน insert พร้อมกัน: อ่านตัวที่ชนะ
            row = dict(conn.execute("SELECT * FROM cinema_imports WHERE idempotency_key=?", (key,)).fetchone())
        _append_history(conn, row["id"], actor, "rendered", "qc_passed", "media QC passed")
        return _record(conn, row["id"]) or row


def confirm_rights(*, import_id: str, actor: str, confirmation: dict[str, Any]) -> dict[str, Any]:
    """ยืนยันสิทธิ์/ความเป็นเจ้าของก่อนขออนุมัติ publish."""
    ensure_tables()
    if not isinstance(confirmation, dict):
        raise TypeError("confirmation is required")
    if confirmation.get("owner_verified") is not True:
        raise ValueError("owner_verified must be true")
    rights_holder = str(confirmation.get("rights_holder", "")).strip()
    license_expires = str(confirmation.get("license_expires", "")).strip()
    age_rating = str(confirmation.get("age_rating", "")).strip()
    if not rights_holder or not license_expires or not age_rating:
        raise ValueError("rights_holder, license_expires and age_rating are required")
    with connect() as conn:
        row = _record(conn, import_id)
        if row is None:
            raise ValueError("import not found")
        if row["status"] not in {"qc_passed", "rights_confirmed"}:
            raise ValueError(f"cannot confirm rights from status {row['status']}")
        conn.execute("UPDATE cinema_imports SET rights_confirmed=1, updated_at=? WHERE id=?", (_now(), import_id))
        _append_history(conn, import_id, actor, row["status"], "rights_confirmed", f"holder={rights_holder[:80]}")
        _append_history(conn, import_id, actor, "rights_confirmed", APPROVAL_PENDING, "awaiting human approval")
        audit_write("cinema.import.rights_confirmed", actor=actor, import_id=import_id, rights_holder=rights_holder[:80])
        result = _record(conn, import_id)
        assert result is not None
        return result


def approve_import(*, import_id: str, actor: str, decision: str, reason: str = "") -> dict[str, Any]:
    """อนุมัติ/ปฏิเสธโดยมนุษย์ (ห้าม publish อัตโนมัติจากการ render)."""
    ensure_tables()
    if decision not in {"approved", "rejected"}:
        raise ValueError("decision must be approved or rejected")
    with connect() as conn:
        row = _record(conn, import_id)
        if row is None:
            raise ValueError("import not found")
        if row["status"] != APPROVAL_PENDING:
            raise ValueError(f"cannot decide from status {row['status']}")
        conn.execute(
            "UPDATE cinema_imports SET approver=?, decision_reason=?, updated_at=? WHERE id=?",
            (actor, (reason or "")[:2000], _now(), import_id),
        )
        _append_history(conn, import_id, actor, APPROVAL_PENDING, decision, (reason or "")[:500])
        result = _record(conn, import_id)
        assert result is not None
        return result


def run_import(
    *,
    import_id: str,
    actor: str,
    transcode_hook: Callable[[str], dict[str, Any]] | None = None,
    poster_hook: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """รัน import หลังได้รับอนุมัติ: transcoding -> poster -> editorial review."""
    ensure_tables()
    with connect() as conn:
        row = _record(conn, import_id)
        if row is None:
            raise ValueError("import not found")
        if row["status"] != "approved":
            raise ValueError(f"import must be approved before run (status={row['status']})")
        conn.execute("UPDATE cinema_imports SET attempts=attempts+1, updated_at=? WHERE id=?", (_now(), import_id))
        _append_history(conn, import_id, actor, "approved", "importing", "import started")
        media_path = row["media_path"]

    # hooks รันนอก transaction เพื่อไม่ lock DB นาน
    try:
        if transcode_hook:
            outcome = transcode_hook(media_path)
            if not isinstance(outcome, dict) or not outcome.get("ok"):
                raise RuntimeError(str(outcome.get("error", "transcode failed")) if isinstance(outcome, dict) else "transcode failed")
        else:
            target = Path(media_path)
            if not target.exists():
                raise RuntimeError("media file missing at import time")
    except Exception as exc:  # noqa: BLE001 - ต้องบันทึกทุกความล้มเหลวเพื่อ retry
        with connect() as conn:
            conn.execute("UPDATE cinema_imports SET last_error=?, updated_at=? WHERE id=?", (str(exc)[:2000], _now(), import_id))
            _append_history(conn, import_id, actor, "importing", "transcode_failed", str(exc)[:500])
            result = _record(conn, import_id)
            assert result is not None
            return result

    try:
        if poster_hook:
            outcome = poster_hook(media_path)
            if not isinstance(outcome, dict) or not outcome.get("ok"):
                raise RuntimeError(str(outcome.get("error", "poster failed")) if isinstance(outcome, dict) else "poster failed")
    except Exception as exc:  # noqa: BLE001
        with connect() as conn:
            conn.execute("UPDATE cinema_imports SET last_error=?, updated_at=? WHERE id=?", (str(exc)[:2000], _now(), import_id))
            _append_history(conn, import_id, actor, "importing", "poster_failed", str(exc)[:500])
            result = _record(conn, import_id)
            assert result is not None
            return result

    with connect() as conn:
        _append_history(conn, import_id, actor, "importing", "editorial_review", "awaiting editorial decision")
        result = _record(conn, import_id)
        assert result is not None
        return result


def editorial_decide(*, import_id: str, actor: str, publish: bool, cinema_film_ref: str = "", note: str = "") -> dict[str, Any]:
    """editorial ตัดสินใจขั้นสุดท้าย: publish หรือ reject."""
    ensure_tables()
    with connect() as conn:
        row = _record(conn, import_id)
        if row is None:
            raise ValueError("import not found")
        if row["status"] != "editorial_review":
            raise ValueError(f"cannot decide editorial from status {row['status']}")
        if publish:
            if not (cinema_film_ref or "").strip():
                raise ValueError("cinema_film_ref is required to publish")
            conn.execute("UPDATE cinema_imports SET cinema_film_ref=?, updated_at=? WHERE id=?", (cinema_film_ref.strip()[:500], _now(), import_id))
            _append_history(conn, import_id, actor, "editorial_review", "published", (note or "")[:500])
        else:
            _append_history(conn, import_id, actor, "editorial_review", "rejected", (note or "")[:500])
        result = _record(conn, import_id)
        assert result is not None
        audit_write("cinema.import.editorial", actor=actor, import_id=import_id, publish=publish)
        return result


def get_import(import_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        row = _record(conn, import_id)
        return dict(row) if row else None


def list_imports(*, project_id: str | None = None, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    ensure_tables()
    limit = max(1, min(limit, 200))
    query = "SELECT * FROM cinema_imports"
    clauses: list[str] = []
    params: list[Any] = []
    if project_id:
        clauses.append("project_id=?")
        params.append(project_id)
    if status:
        clauses.append("status=?")
        params.append(status)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        return [dict(row) for row in conn.execute(query, tuple(params)).fetchall()]
