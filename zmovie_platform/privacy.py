"""Privacy: data export and account deletion (with audit trail preserved)."""
from __future__ import annotations

from typing import Any

from .audit import write as audit_write
from .storage import connect


def export_user_data(username: str) -> dict[str, Any]:
    """รวบรวมข้อมูลของผู้ใช้เพื่อส่งออก (projects, jobs, assets, subscriptions, ledger)."""
    name = username.strip().lower()
    if not name:
        raise ValueError("username is required")
    with connect() as conn:
        user = conn.execute("SELECT id, username, role, created_at FROM users WHERE username=?", (name,)).fetchone()
        if user is None:
            raise ValueError("user not found")
        user_dict = dict(user)
        projects = [dict(r) for r in conn.execute("SELECT * FROM projects WHERE owner=?", (name,)).fetchall()]
        project_ids = [p["id"] for p in projects]
        jobs: list[dict[str, Any]] = []
        assets: list[dict[str, Any]] = []
        for pid in project_ids:
            jobs.extend(dict(r) for r in conn.execute("SELECT * FROM render_jobs WHERE project_id=?", (pid,)).fetchall())
            assets.extend(dict(r) for r in conn.execute("SELECT * FROM assets WHERE project_id=?", (pid,)).fetchall())
        subs = [dict(r) for r in conn.execute("SELECT * FROM commerce_subscriptions WHERE user_id=?", (name,)).fetchall()]
        ledger = [dict(r) for r in conn.execute("SELECT * FROM commerce_ledger WHERE user_id=?", (name,)).fetchall()]
        holds = [dict(r) for r in conn.execute("SELECT * FROM ticket_holds WHERE holder_ref=?", (name,)).fetchall()]
        reservations = [dict(r) for r in conn.execute("SELECT * FROM ticket_reservations WHERE holder_ref=?", (name,)).fetchall()]
    audit_write("privacy.export", actor=name)
    return {
        "user": {**user_dict, "password_hash": "[REDACTED]"},
        "projects": projects,
        "render_jobs": jobs,
        "assets": assets,
        "commerce_subscriptions": subs,
        "commerce_ledger": ledger,
        "ticket_holds": holds,
        "ticket_reservations": reservations,
    }


def delete_user_data(username: str, *, confirmation: str) -> dict[str, Any]:
    """ลบข้อมูลผู้ใช้ทั้งหมด (ต้องยืนยันด้วยชื่อผู้ใช้ซ้ำ).

    Audit log ในไฟล์ (audit.jsonl) ถูกเก็บไว้เพื่อความสมบูรณ์ของบันทึก
    แต่ข้อมูลระบุตัวตนใน DB ถูกลบทั้งหมด.
    """
    name = username.strip().lower()
    if confirmation.strip().lower() != name or not name:
        raise ValueError("confirmation must repeat the username exactly")
    with connect() as conn:
        user = conn.execute("SELECT id FROM users WHERE username=?", (name,)).fetchone()
        if user is None:
            raise ValueError("user not found")
        project_ids = [r["id"] for r in conn.execute("SELECT id FROM projects WHERE owner=?", (name,)).fetchall()]
        for pid in project_ids:
            conn.execute("DELETE FROM projects WHERE id=?", (pid,))
        conn.execute("DELETE FROM commerce_subscriptions WHERE user_id=?", (name,))
        conn.execute("DELETE FROM commerce_ledger WHERE user_id=?", (name,))
        conn.execute("DELETE FROM ticket_holds WHERE holder_ref=?", (name,))
        conn.execute("DELETE FROM ticket_reservations WHERE holder_ref=?", (name,))
        conn.execute("DELETE FROM users WHERE username=?", (name,))
        removed = {"projects": len(project_ids)}
    audit_write("privacy.account_deleted", actor=name, removed_projects=removed["projects"])
    return {"deleted_user": name, **removed}
