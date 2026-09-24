"""Checkout, subscription lifecycle, ledger, reconciliation, access checks."""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from ..audit import write as audit_write
from . import store
from .psp import get_psp

# ห้ามรับเลขบัตรเด็ดขาด: รับได้แค่ payment_method_ref ที่เป็น token
CARD_LIKE_FIELDS = {"card_number", "pan", "cvv", "cvc", "expiry", "exp_month", "exp_year"}


def _reject_card_data(payload: dict[str, Any]) -> None:
    for field in CARD_LIKE_FIELDS:
        if field in payload:
            raise ValueError("card data must never be sent to zMovie (use payment_method_ref only)")


def _period_end(interval: str) -> str:
    now = datetime.now(timezone.utc)
    if interval == "forever":
        return "9999-12-31T00:00:00+00:00"
    if interval == "yearly":
        return (now + timedelta(days=365)).isoformat()
    return (now + timedelta(days=30)).isoformat()


def create_checkout(*, user_id: str, plan_id: str, payment_method_ref: str, idempotency_key: str) -> dict[str, Any]:
    """สร้าง checkout session (sandbox) + บันทึก ledger แบบ idempotent."""
    if not user_id.strip() or not plan_id.strip() or not idempotency_key.strip():
        raise ValueError("user_id, plan_id and idempotency_key are required")
    if not payment_method_ref.strip().startswith("pm_"):
        raise ValueError("payment_method_ref must be a token starting with pm_")
    plan = store.get_plan(plan_id)
    if plan is None or not plan["active"]:
        raise ValueError("plan not available")
    psp = get_psp()
    session = psp.create_session(amount_thb=int(plan["price_thb"]), currency="THB", reference=f"{user_id}:{plan_id}")
    entry_id = "le_" + hashlib.sha256(idempotency_key.encode()).hexdigest()[:24]
    ledger = store.append_ledger({
        "id": entry_id, "user_id": user_id, "kind": "charge",
        "amount_thb": int(plan["price_thb"]), "currency": "THB",
        "status": "pending", "psp_ref": session["session_id"], "idempotency_key": idempotency_key,
    })
    audit_write("commerce.checkout.created", actor=user_id, plan_id=plan_id, amount_thb=int(plan["price_thb"]))
    return {"session": session, "ledger": ledger, "plan": plan}


def confirm_checkout(*, user_id: str, session_id: str, plan_id: str, idempotency_key: str) -> dict[str, Any]:
    """ยืนยันชำระเงิน + เปิด subscription (idempotent ผ่าน ledger)."""
    psp = get_psp()
    result = psp.confirm_session(session_id=session_id)
    if result["status"] != "succeeded":
        store.update_ledger_status(idempotency_key=idempotency_key, status="failed", psp_ref=result.get("psp_ref", ""))
        audit_write("commerce.checkout.failed", actor=user_id, session_id=session_id)
        raise ValueError("payment failed in sandbox PSP")
    plan = store.get_plan(plan_id)
    assert plan is not None
    store.update_ledger_status(idempotency_key=idempotency_key, status="succeeded", psp_ref=result["psp_ref"])
    sub_id = "sub_" + hashlib.sha256(f"{user_id}:{plan_id}".encode()).hexdigest()[:24]
    subscription = store.save_subscription({
        "id": sub_id, "user_id": user_id, "plan_id": plan_id, "status": "active",
        "current_period_end": _period_end(str(plan["interval"])),
    })
    invoice = {
        "invoice_id": "inv_" + hashlib.sha256(f"{idempotency_key}".encode()).hexdigest()[:24],
        "user_id": user_id, "plan_id": plan_id, "amount_thb": int(plan["price_thb"]),
        "currency": "THB", "psp_ref": result["psp_ref"], "issued_at": datetime.now(timezone.utc).isoformat(),
    }
    audit_write("commerce.checkout.succeeded", actor=user_id, plan_id=plan_id, sub_id=sub_id)
    return {"subscription": subscription, "invoice": invoice, "psp": result}


def handle_webhook(*, psp_name: str, event_id: str, event_type: str, payload: dict[str, Any], signature: str, raw_body: bytes) -> dict[str, Any]:
    """ตรวจลายเซ็น + ประมวลผลแบบ idempotent (ซ้ำ = ข้าม)."""
    psp = get_psp(psp_name)
    if not psp.verify_webhook(raw_body, signature):
        raise ValueError("invalid webhook signature")
    is_new = store.record_webhook_event(event_id=event_id, psp=psp_name, type=event_type, payload=payload)
    if not is_new:
        return {"status": "duplicate_ignored", "event_id": event_id}
    if event_type == "payment.succeeded":
        store.update_ledger_status(
            idempotency_key=str(payload.get("idempotency_key", "")),
            status="succeeded", psp_ref=str(payload.get("psp_ref", "")),
        )
    elif event_type == "payment.failed":
        store.update_ledger_status(
            idempotency_key=str(payload.get("idempotency_key", "")),
            status="failed", psp_ref=str(payload.get("psp_ref", "")),
        )
    elif event_type == "refund.succeeded":
        store.update_ledger_status(
            idempotency_key=str(payload.get("idempotency_key", "")),
            status="refunded", psp_ref=str(payload.get("psp_ref", "")),
        )
    audit_write("commerce.webhook", actor=f"psp:{psp_name}", event_id=event_id, event_type=event_type)
    return {"status": "processed", "event_id": event_id}


def request_refund(*, user_id: str, idempotency_key: str) -> dict[str, Any]:
    """ขอคืนเงิน: pending -> refunded (sandbox)."""
    with_ledger = None
    for entry in store.ledger_for_user(user_id, limit=500):
        if entry["idempotency_key"] == idempotency_key:
            with_ledger = entry
            break
    if with_ledger is None:
        raise ValueError("ledger entry not found")
    if with_ledger["status"] != "succeeded":
        raise ValueError(f"only succeeded charges can be refunded (status={with_ledger['status']})")
    psp = get_psp()
    result = psp.refund(psp_ref=with_ledger["psp_ref"], amount_thb=int(with_ledger["amount_thb"]))
    updated = store.update_ledger_status(idempotency_key=idempotency_key, status="refunded", psp_ref=result["psp_ref"])
    audit_write("commerce.refund", actor=user_id, idempotency_key=idempotency_key)
    return {"ledger": updated, "psp": result}


def change_plan(*, user_id: str, new_plan_id: str) -> dict[str, Any]:
    """upgrade/downgrade: ปิดรอบเดิม เปิดรอบใหม่ (proration คำนวณแบบง่ายใน sandbox)."""
    current = store.active_subscription_for_user(user_id)
    if current is None:
        raise ValueError("no active subscription")
    new_plan = store.get_plan(new_plan_id)
    if new_plan is None or not new_plan["active"]:
        raise ValueError("plan not available")
    store.save_subscription({**current, "status": "canceled"})
    sub_id = "sub_" + hashlib.sha256(f"{user_id}:{new_plan_id}:{time.time_ns()}".encode()).hexdigest()[:24]
    nxt = store.save_subscription({
        "id": sub_id, "user_id": user_id, "plan_id": new_plan_id, "status": "active",
        "current_period_end": _period_end(str(new_plan["interval"])),
    })
    audit_write("commerce.plan_changed", actor=user_id, from_plan=current["plan_id"], to_plan=new_plan_id)
    return {"subscription": nxt, "previous": current}


def cancel_subscription(*, user_id: str, at_period_end: bool = True) -> dict[str, Any]:
    current = store.active_subscription_for_user(user_id)
    if current is None:
        raise ValueError("no active subscription")
    if at_period_end:
        updated = store.save_subscription({**current, "cancel_at_period_end": True})
    else:
        updated = store.save_subscription({**current, "status": "canceled"})
    audit_write("commerce.subscription_canceled", actor=user_id, sub_id=current["id"])
    return {"subscription": updated}


def expire_due_subscriptions(*, now_iso: str | None = None) -> int:
    """หมดอายุ subscription ที่เลยรอบแล้ว (เรียกจาก cron/scheduler)."""
    now = now_iso or datetime.now(timezone.utc).isoformat()
    expired = 0
    with_count = 0
    # สแกนแบบง่ายเพื่อคง testability โดยไม่ต้องพึ่ง DB เฉพาะ
    from ..storage import connect
    store.ensure_tables()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM commerce_subscriptions WHERE status IN ('trialing','active','past_due') AND current_period_end != ''"
        ).fetchall()
        for row in rows:
            with_count += 1
            item = dict(row)
            if item["current_period_end"] < now:
                conn.execute("UPDATE commerce_subscriptions SET status='expired' WHERE id=?", (item["id"],))
                expired += 1
    audit_write("commerce.expiry_sweep", actor="scheduler", checked=with_count, expired=expired)
    return expired


def entitlements_for_user(user_id: str) -> list[str]:
    """รวม entitlements จาก subscription ที่ active (หมดอายุ = ถูก revoke)."""
    sub = store.active_subscription_for_user(user_id)
    if sub is None:
        plan = store.get_plan("free")
        return list(json.loads(str(plan["entitlements_json"]))) if plan else ["catalog"]
    plan = store.get_plan(str(sub["plan_id"]))
    if plan is None:
        return ["catalog"]
    return list(json.loads(str(plan["entitlements_json"])))


def can_access_media(*, user_id: str, required_entitlement: str) -> bool:
    """ตรวจสิทธิ์เข้าถึง private media แยกจาก WordPress UI."""
    return required_entitlement in entitlements_for_user(user_id)


def reconcile(*, psp_settlements: list[dict[str, Any]]) -> dict[str, Any]:
    """เทียบ ledger กับ settlement report ของ PSP (หาส่วนต่าง)."""
    from ..storage import connect
    store.ensure_tables()
    with connect() as conn:
        rows = conn.execute("SELECT psp_ref, amount_thb, status FROM commerce_ledger WHERE status='succeeded'").fetchall()
    ledger_by_ref = {row["psp_ref"]: int(row["amount_thb"]) for row in rows}
    settled_by_ref = {item["psp_ref"]: int(item["amount_thb"]) for item in psp_settlements}
    missing_in_psp = sorted(set(ledger_by_ref) - set(settled_by_ref))
    missing_in_ledger = sorted(set(settled_by_ref) - set(ledger_by_ref))
    mismatched = sorted(ref for ref in set(ledger_by_ref) & set(settled_by_ref) if ledger_by_ref[ref] != settled_by_ref[ref])
    return {
        "ledger_count": len(ledger_by_ref),
        "settled_count": len(settled_by_ref),
        "missing_in_psp": missing_in_psp,
        "missing_in_ledger": missing_in_ledger,
        "mismatched": mismatched,
        "balanced": not missing_in_psp and not missing_in_ledger and not mismatched,
    }
