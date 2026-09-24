"""Atomic holds, reservations, checkout lifecycle, check-in, cancel/refund states."""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from .. import storage
from ..models import utcnow
from ..storage import connect
from . import store
from .qr import issue_qr, verify_qr

HOLD_TTL_MINUTES = 10
VALID_SEAT = ("standard", "premium", "accessible")


def _now() -> str:
    return utcnow()


def _new_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256(":".join(parts).encode()).hexdigest()[:24]
    return f"{prefix}_{digest}"


def _immediate() -> Any:
    """SQLite immediate transaction (writer lock) สำหรับกัน double-sell."""
    store.ensure_tables()
    conn = sqlite3.connect(storage.DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("BEGIN IMMEDIATE")
    return conn


def seat_map(auditorium_id: str) -> list[dict[str, Any]]:
    store.ensure_tables()
    with connect() as conn:
        rows = conn.execute(
            "SELECT seat_no, kind, active FROM ticket_seats WHERE auditorium_id=? ORDER BY seat_no", (auditorium_id,)
        ).fetchall()
        return [dict(row) for row in rows]


def availability(showtime_id: str) -> dict[str, Any]:
    """คืนที่นั่งว่าง = ผังทั้งหมด - reserved - holds ที่ยังไม่หมดอายุ/ไม่ถูกใช้."""
    store.ensure_tables()
    now = _now()
    with connect() as conn:
        show = store._row(conn, "SELECT * FROM ticket_showtimes WHERE id=?", (showtime_id,))
        if show is None:
            raise ValueError("showtime not found")
        seats = [dict(r) for r in conn.execute(
            "SELECT seat_no FROM ticket_seats WHERE auditorium_id=? AND active=1", (show["auditorium_id"],)).fetchall()]
        reserved = {r["seat_no"] for r in conn.execute(
            "SELECT seat_no FROM ticket_reservations WHERE showtime_id=? AND status IN ('held','confirmed')", (showtime_id,)).fetchall()}
        held = {r["seat_no"] for r in conn.execute(
            "SELECT seat_no FROM ticket_holds WHERE showtime_id=? AND consumed=0 AND expires_at > ?", (showtime_id, now)).fetchall()}
        taken = reserved | held
        free = [s["seat_no"] for s in seats if s["seat_no"] not in taken]
        return {"showtime_id": showtime_id, "total": len(seats), "taken": sorted(taken), "available": sorted(free)}


def hold_seat(*, showtime_id: str, seat_no: str, holder_ref: str, idempotency_key: str,
              ttl_minutes: int = HOLD_TTL_MINUTES) -> dict[str, Any]:
    """จองชั่วคราวแบบ atomic (idempotent ตาม idempotency_key)."""
    store.ensure_tables()
    if not holder_ref.strip() or not idempotency_key.strip():
        raise ValueError("holder_ref and idempotency_key are required")
    seat_no = seat_no.strip().upper()
    conn = _immediate()
    try:
        dup = conn.execute("SELECT * FROM ticket_holds WHERE idempotency_key=?", (idempotency_key,)).fetchone()
        if dup:
            result = dict(dup)
            conn.commit()
            return result
        show = conn.execute("SELECT * FROM ticket_showtimes WHERE id=?", (showtime_id,)).fetchone()
        if show is None:
            raise ValueError("showtime not found")
        if show["status"] != "scheduled":
            raise ValueError(f"showtime not bookable (status={show['status']})")
        seat = conn.execute(
            "SELECT * FROM ticket_seats WHERE auditorium_id=? AND seat_no=? AND active=1",
            (show["auditorium_id"], seat_no)).fetchone()
        if seat is None:
            raise ValueError("seat not found")
        now = _now()
        taken = conn.execute(
            "SELECT 1 FROM ticket_reservations WHERE showtime_id=? AND seat_no=? AND status IN ('held','confirmed')",
            (showtime_id, seat_no)).fetchone()
        if taken:
            raise ValueError("seat already reserved")
        active_hold = conn.execute(
            "SELECT 1 FROM ticket_holds WHERE showtime_id=? AND seat_no=? AND consumed=0 AND expires_at > ?",
            (showtime_id, seat_no, now)).fetchone()
        if active_hold:
            raise ValueError("seat already on hold")
        hold_id = _new_id("hold", showtime_id, seat_no, idempotency_key)
        expires = (datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).isoformat()
        conn.execute(
            "INSERT INTO ticket_holds(id,showtime_id,seat_no,holder_ref,idempotency_key,expires_at,created_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (hold_id, showtime_id, seat_no, holder_ref.strip(), idempotency_key.strip(), expires, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM ticket_holds WHERE id=?", (hold_id,)).fetchone()
        result = dict(row)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    # audit หลังปิด write-transaction เพื่อลด contention
    store.audit("ticket.hold", actor=holder_ref, showtime_id=showtime_id, seat_no=seat_no)
    return result


def release_expired_holds(*, now_iso: str | None = None) -> int:
    store.ensure_tables()
    now = now_iso or _now()
    with connect() as conn:
        cur = conn.execute("DELETE FROM ticket_holds WHERE consumed=0 AND expires_at <= ?", (now,))
        count = cur.rowcount
    if count:
        store.audit("ticket.hold_expired_sweep", swept=count)
    return count


def confirm_hold(*, hold_id: str, holder_ref: str, idempotency_key: str) -> dict[str, Any]:
    """เปลี่ยน hold -> reservation + ticket แบบ atomic (กัน double-sell ด้วย UNIQUE)."""
    store.ensure_tables()
    conn = _immediate()
    try:
        dup = conn.execute("SELECT * FROM ticket_reservations WHERE idempotency_key=?", (idempotency_key,)).fetchone()
        if dup:
            res = dict(dup)
            ticket = conn.execute("SELECT * FROM ticket_tickets WHERE reservation_id=?", (res["id"],)).fetchone()
            conn.commit()
            return {"reservation": res, "ticket": dict(ticket) if ticket else None, "duplicate": True}
        hold = conn.execute("SELECT * FROM ticket_holds WHERE id=?", (hold_id,)).fetchone()
        if hold is None:
            raise ValueError("hold not found")
        hold = dict(hold)
        if hold["holder_ref"] != holder_ref:
            raise ValueError("hold owner mismatch")
        if hold["consumed"]:
            raise ValueError("hold already consumed")
        if hold["expires_at"] <= _now():
            raise ValueError("hold expired")
        res_id = _new_id("res", hold["showtime_id"], hold["seat_no"], idempotency_key)
        now = _now()
        try:
            conn.execute(
                "INSERT INTO ticket_reservations(id,showtime_id,seat_no,holder_ref,hold_id,status,idempotency_key,created_at,updated_at)"
                " VALUES(?,?,?,?,?,?,?,?,?)",
                (res_id, hold["showtime_id"], hold["seat_no"], holder_ref, hold_id, "confirmed", idempotency_key, now, now),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("seat already reserved (concurrent booking rejected)") from exc
        conn.execute("UPDATE ticket_holds SET consumed=1 WHERE id=?", (hold_id,))
        qr = issue_qr(ticket_id=f"tkt_{res_id[4:]}", showtime_id=hold["showtime_id"], seat_no=hold["seat_no"])
        ticket_id = f"tkt_{res_id[4:]}"
        conn.execute(
            "INSERT INTO ticket_tickets(id,reservation_id,qr_payload,qr_signature,status,created_at) VALUES(?,?,?,?,?,?)",
            (ticket_id, res_id, qr["qr_payload"], qr["qr_signature"], "issued", now),
        )
        conn.commit()
        res = dict(conn.execute("SELECT * FROM ticket_reservations WHERE id=?", (res_id,)).fetchone())
        # อ่าน ticket ผ่าน connection เดิมก่อนปิด (ลด round-trip)
        tkt = conn.execute("SELECT * FROM ticket_tickets WHERE reservation_id=?", (res_id,)).fetchone()
        ticket = dict(tkt)
    except Exception:
        try:
            conn.rollback()
        except sqlite3.Error:
            pass
        raise
    finally:
        conn.close()
    # audit หลังปิด write-transaction เพื่อลด contention
    store.audit("ticket.reserved", actor=holder_ref, reservation_id=res_id, seat_no=hold["seat_no"])
    return {"reservation": res, "ticket": ticket, "duplicate": False}


def cancel_reservation(*, reservation_id: str, holder_ref: str) -> dict[str, Any]:
    store.ensure_tables()
    with connect() as conn:
        row = store._row(conn, "SELECT * FROM ticket_reservations WHERE id=?", (reservation_id,))
        if row is None:
            raise ValueError("reservation not found")
        if row["holder_ref"] != holder_ref:
            raise ValueError("reservation owner mismatch")
        if row["status"] not in {"held", "confirmed"}:
            raise ValueError(f"cannot cancel from status {row['status']}")
        conn.execute("UPDATE ticket_reservations SET status='canceled', updated_at=? WHERE id=?", (_now(), reservation_id))
        conn.execute("UPDATE ticket_tickets SET status='void' WHERE reservation_id=?", (reservation_id,))
        updated = store._row(conn, "SELECT * FROM ticket_reservations WHERE id=?", (reservation_id,))
        assert updated is not None
        result = updated
    store.audit("ticket.canceled", actor=holder_ref, reservation_id=reservation_id)
    return result


def mark_refunded(*, reservation_id: str, actor: str) -> dict[str, Any]:
    store.ensure_tables()
    with connect() as conn:
        row = store._row(conn, "SELECT * FROM ticket_reservations WHERE id=?", (reservation_id,))
        if row is None:
            raise ValueError("reservation not found")
        if row["status"] != "canceled":
            raise ValueError("only canceled reservations can transition to refunded")
        conn.execute("UPDATE ticket_reservations SET status='refunded', updated_at=? WHERE id=?", (_now(), reservation_id))
        updated = store._row(conn, "SELECT * FROM ticket_reservations WHERE id=?", (reservation_id,))
        assert updated is not None
        result = updated
    store.audit("ticket.refunded", actor=actor, reservation_id=reservation_id)
    return result


def check_in(*, qr_payload: str, qr_signature: str, actor: str) -> dict[str, Any]:
    payload = verify_qr(qr_payload=qr_payload, qr_signature=qr_signature)
    if payload is None:
        raise ValueError("invalid or expired ticket QR")
    store.ensure_tables()
    with connect() as conn:
        tkt = store._row(conn, "SELECT * FROM ticket_tickets WHERE qr_payload=?", (qr_payload,))
        if tkt is None:
            raise ValueError("ticket not found")
        if tkt["status"] == "checked_in":
            return {"status": "duplicate_check_in", "ticket": tkt}
        if tkt["status"] != "issued":
            raise ValueError(f"ticket not usable (status={tkt['status']})")
        now = _now()
        conn.execute("UPDATE ticket_tickets SET status='checked_in', checked_in_at=? WHERE id=?", (now, tkt["id"]))
        updated = store._row(conn, "SELECT * FROM ticket_tickets WHERE id=?", (tkt["id"],))
        assert updated is not None
        result = {"status": "checked_in", "ticket": updated}
    store.audit("ticket.checked_in", actor=actor, ticket_id=result["ticket"]["id"])
    return result
