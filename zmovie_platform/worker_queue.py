from __future__ import annotations

import json
import os
import socket
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from .storage import connect, dumps, loads

ACTIVE_STATES = {"queued", "claimed", "running", "retry_wait", "recovery_required"}
TERMINAL_STATES = {"completed", "failed", "cancelled"}
SENSITIVE_KEYS = {"password", "secret", "token", "cookie", "authorization", "browser_state", "storage_state"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _after(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=max(1, seconds))).isoformat()


def worker_identity() -> str:
    return f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"


def _sanitize_payload(value: Any, path: str = "payload") -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in SENSITIVE_KEYS):
                raise ValueError(f"sensitive field not allowed in worker payload: {path}.{key}")
            out[str(key)] = _sanitize_payload(item, f"{path}.{key}")
        return out
    if isinstance(value, list):
        return [_sanitize_payload(item, f"{path}[]") for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"unsupported worker payload type at {path}")


def enqueue(
    job_type: str,
    *,
    project_id: str = "",
    production_run_id: str = "",
    provider: str = "",
    payload: dict[str, Any] | None = None,
    priority: int = 100,
    max_attempts: int = 3,
) -> dict[str, Any]:
    payload = _sanitize_payload(payload or {})
    now = _now()
    job_id = f"wrk_{uuid.uuid4().hex[:16]}"
    with connect() as conn:
        conn.execute(
            "INSERT INTO worker_jobs(id,job_type,project_id,production_run_id,provider,payload_json,status,priority,attempts,max_attempts,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?, 'queued', ?,0,?,?,?)",
            (
                job_id,
                str(job_type),
                str(project_id),
                str(production_run_id),
                str(provider),
                dumps(payload),
                int(priority),
                max(1, int(max_attempts)),
                now,
                now,
            ),
        )
    return get(job_id) or {"id": job_id, "status": "queued"}


def get(job_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM worker_jobs WHERE id=?", (job_id,)).fetchone()
    if row is None:
        return None
    item = dict(row)
    item["payload"] = loads(item.pop("payload_json", "{}"), {})
    item["result"] = loads(item.pop("result_json", "{}"), {})
    return item


def list_jobs(limit: int = 200, status: str = "") -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 1000))
    with connect() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM worker_jobs WHERE status=? ORDER BY priority ASC, created_at ASC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM worker_jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["payload"] = loads(item.pop("payload_json", "{}"), {})
        item["result"] = loads(item.pop("result_json", "{}"), {})
        result.append(item)
    return result


def claim(worker_id: str, *, lease_seconds: int = 120, allowed_types: tuple[str, ...] = ()) -> dict[str, Any] | None:
    now = _now()
    lease = _after(lease_seconds)
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        sql = (
            "SELECT id FROM worker_jobs WHERE "
            "((status='queued') OR (status='retry_wait' AND (next_attempt_at='' OR next_attempt_at<=?)))"
        )
        params: list[Any] = [now]
        if allowed_types:
            placeholders = ",".join("?" for _ in allowed_types)
            sql += f" AND job_type IN ({placeholders})"
            params.extend(allowed_types)
        sql += " ORDER BY priority ASC, created_at ASC LIMIT 1"
        row = conn.execute(sql, tuple(params)).fetchone()
        if row is None:
            return None
        job_id = str(row["id"])
        cur = conn.execute(
            "UPDATE worker_jobs SET status='claimed',worker_id=?,claimed_at=?,heartbeat_at=?,lease_expires_at=?,updated_at=? "
            "WHERE id=? AND status IN ('queued','retry_wait')",
            (worker_id, now, now, lease, now, job_id),
        )
        if cur.rowcount != 1:
            return None
    return get(job_id)


def mark_running(job_id: str, worker_id: str, *, lease_seconds: int = 120) -> None:
    now = _now()
    with connect() as conn:
        cur = conn.execute(
            "UPDATE worker_jobs SET status='running',started_at=CASE WHEN started_at='' THEN ? ELSE started_at END,heartbeat_at=?,lease_expires_at=?,updated_at=? "
            "WHERE id=? AND worker_id=? AND status='claimed'",
            (now, now, _after(lease_seconds), now, job_id, worker_id),
        )
        if cur.rowcount != 1:
            raise RuntimeError("worker job cannot transition to running")


def heartbeat(job_id: str, worker_id: str, *, lease_seconds: int = 120) -> bool:
    now = _now()
    with connect() as conn:
        cur = conn.execute(
            "UPDATE worker_jobs SET heartbeat_at=?,lease_expires_at=?,updated_at=? WHERE id=? AND worker_id=? AND status IN ('claimed','running')",
            (now, _after(lease_seconds), now, job_id, worker_id),
        )
        return cur.rowcount == 1


def complete(job_id: str, worker_id: str, result: dict[str, Any] | None = None) -> None:
    now = _now()
    with connect() as conn:
        conn.execute(
            "UPDATE worker_jobs SET status='completed',result_json=?,completed_at=?,heartbeat_at=?,lease_expires_at='',updated_at=? "
            "WHERE id=? AND worker_id=?",
            (dumps(result or {}), now, now, now, job_id, worker_id),
        )


def fail(job_id: str, worker_id: str, exc: BaseException, *, retry_delay_seconds: int = 30) -> dict[str, Any]:
    now = _now()
    with connect() as conn:
        row = conn.execute("SELECT attempts,max_attempts FROM worker_jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise ValueError("worker job not found")
        attempts = int(row["attempts"] or 0) + 1
        max_attempts = max(1, int(row["max_attempts"] or 1))
        retry = attempts < max_attempts
        status = "retry_wait" if retry else "failed"
        conn.execute(
            "UPDATE worker_jobs SET status=?,attempts=?,next_attempt_at=?,failed_at=?,error_code=?,error_message=?,worker_id='',lease_expires_at='',updated_at=? WHERE id=?",
            (
                status,
                attempts,
                _after(retry_delay_seconds) if retry else "",
                "" if retry else now,
                type(exc).__name__,
                str(exc)[:1000],
                now,
                job_id,
            ),
        )
    return get(job_id) or {}


def recover_stale(*, apply: bool = False) -> list[dict[str, Any]]:
    now = _now()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM worker_jobs WHERE status IN ('claimed','running') AND lease_expires_at<>'' AND lease_expires_at<? ORDER BY created_at",
            (now,),
        ).fetchall()
        found = [dict(row) for row in rows]
        if apply:
            for row in rows:
                job_id = str(row["id"])
                attempts = int(row["attempts"] or 0) + 1
                max_attempts = max(1, int(row["max_attempts"] or 1))
                if str(row["job_type"]) == "bilibili_publish":
                    status = "recovery_required"
                    next_attempt = ""
                    code = "external_state_unknown"
                elif attempts < max_attempts:
                    status = "retry_wait"
                    next_attempt = now
                    code = "stale_lease_recovered"
                else:
                    status = "failed"
                    next_attempt = ""
                    code = "retry_exhausted_after_stale_lease"
                conn.execute(
                    "UPDATE worker_jobs SET status=?,attempts=?,worker_id='',lease_expires_at='',next_attempt_at=?,error_code=?,error_message=?,updated_at=? WHERE id=?",
                    (status, attempts, next_attempt, code, "worker lease expired", now, job_id),
                )
    return found


def set_paused(paused: bool) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO runtime_state(key,value,updated_at) VALUES('worker_paused',?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
            ("1" if paused else "0", _now()),
        )


def is_paused() -> bool:
    with connect() as conn:
        row = conn.execute("SELECT value FROM runtime_state WHERE key='worker_paused'").fetchone()
    return bool(row and str(row["value"]) == "1")


def queue_status() -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute("SELECT status,COUNT(*) AS n FROM worker_jobs GROUP BY status").fetchall()
    counts = {str(row["status"]): int(row["n"]) for row in rows}
    return {"paused": is_paused(), "counts": counts, "active": sum(counts.get(s, 0) for s in ACTIVE_STATES)}
