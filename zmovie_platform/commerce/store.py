"""Commerce persistence (SQLite, append-only ledger, idempotent webhooks)."""
from __future__ import annotations

import json
from typing import Any

from ..models import utcnow
from ..storage import connect

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS commerce_plans (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  kind TEXT NOT NULL,
  price_thb INTEGER NOT NULL DEFAULT 0,
  interval TEXT NOT NULL DEFAULT 'monthly',
  entitlements_json TEXT NOT NULL DEFAULT '[]',
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commerce_subscriptions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  plan_id TEXT NOT NULL REFERENCES commerce_plans(id),
  status TEXT NOT NULL,
  current_period_end TEXT NOT NULL DEFAULT '',
  cancel_at_period_end INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commerce_ledger (
  id TEXT PRIMARY KEY,
  subscription_id TEXT NOT NULL DEFAULT '',
  user_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  amount_thb INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'THB',
  status TEXT NOT NULL,
  psp_ref TEXT NOT NULL DEFAULT '',
  idempotency_key TEXT UNIQUE NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commerce_webhook_events (
  event_id TEXT PRIMARY KEY,
  psp TEXT NOT NULL,
  type TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  received_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_commerce_subs_user ON commerce_subscriptions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_commerce_ledger_user ON commerce_ledger(user_id, created_at);
"""


def ensure_tables() -> None:
    with connect() as conn:
        conn.executescript(TABLE_SQL)


def _row(conn: Any, query: str, params: tuple = ()) -> dict[str, Any] | None:
    row = conn.execute(query, params).fetchone()
    return dict(row) if row else None


def upsert_plan(plan: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    now = utcnow()
    with connect() as conn:
        conn.execute(
            "INSERT INTO commerce_plans(id,name,kind,price_thb,interval,entitlements_json,active,created_at)"
            " VALUES(?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET name=excluded.name,kind=excluded.kind,price_thb=excluded.price_thb,"
            "interval=excluded.interval,entitlements_json=excluded.entitlements_json,active=excluded.active",
            (
                plan["id"], plan["name"], plan["kind"], int(plan.get("price_thb", 0)),
                plan.get("interval", "monthly"), json.dumps(plan.get("entitlements", []), ensure_ascii=False),
                1 if plan.get("active", True) else 0, now,
            ),
        )
        row = _row(conn, "SELECT * FROM commerce_plans WHERE id=?", (plan["id"],))
        assert row is not None
        return row


def get_plan(plan_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM commerce_plans WHERE id=?", (plan_id,))


def list_plans(*, active_only: bool = True) -> list[dict[str, Any]]:
    ensure_tables()
    with connect() as conn:
        if active_only:
            rows = conn.execute("SELECT * FROM commerce_plans WHERE active=1 ORDER BY price_thb").fetchall()
        else:
            rows = conn.execute("SELECT * FROM commerce_plans ORDER BY price_thb").fetchall()
        return [dict(row) for row in rows]


def save_subscription(sub: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    now = utcnow()
    with connect() as conn:
        conn.execute(
            "INSERT INTO commerce_subscriptions(id,user_id,plan_id,status,current_period_end,cancel_at_period_end,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET plan_id=excluded.plan_id,status=excluded.status,"
            "current_period_end=excluded.current_period_end,cancel_at_period_end=excluded.cancel_at_period_end,updated_at=excluded.updated_at",
            (
                sub["id"], sub["user_id"], sub["plan_id"], sub["status"],
                sub.get("current_period_end", ""), 1 if sub.get("cancel_at_period_end") else 0,
                sub.get("created_at", now), now,
            ),
        )
        row = _row(conn, "SELECT * FROM commerce_subscriptions WHERE id=?", (sub["id"],))
        assert row is not None
        return row


def get_subscription(sub_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM commerce_subscriptions WHERE id=?", (sub_id,))


def active_subscription_for_user(user_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(
            conn,
            "SELECT * FROM commerce_subscriptions WHERE user_id=? AND status IN ('trialing','active','past_due') ORDER BY updated_at DESC LIMIT 1",
            (user_id,),
        )


def append_ledger(entry: dict[str, Any]) -> dict[str, Any]:
    """Append-only: ซ้ำ idempotency_key คืน record เดิม (กัน double-charge)."""
    ensure_tables()
    now = utcnow()
    with connect() as conn:
        conn.execute(
            "INSERT INTO commerce_ledger(id,subscription_id,user_id,kind,amount_thb,currency,status,psp_ref,idempotency_key,created_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(idempotency_key) DO NOTHING",
            (
                entry["id"], entry.get("subscription_id", ""), entry["user_id"], entry["kind"],
                int(entry["amount_thb"]), entry.get("currency", "THB"), entry["status"],
                entry.get("psp_ref", ""), entry["idempotency_key"], entry.get("created_at", now),
            ),
        )
        row = _row(conn, "SELECT * FROM commerce_ledger WHERE idempotency_key=?", (entry["idempotency_key"],))
        assert row is not None
        return row


def update_ledger_status(*, idempotency_key: str, status: str, psp_ref: str = "") -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        conn.execute(
            "UPDATE commerce_ledger SET status=?, psp_ref=? WHERE idempotency_key=?",
            (status, psp_ref, idempotency_key),
        )
        return _row(conn, "SELECT * FROM commerce_ledger WHERE idempotency_key=?", (idempotency_key,))


def ledger_for_user(user_id: str, limit: int = 100) -> list[dict[str, Any]]:
    ensure_tables()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM commerce_ledger WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (user_id, max(1, min(limit, 500)))
        ).fetchall()
        return [dict(row) for row in rows]


def record_webhook_event(*, event_id: str, psp: str, type: str, payload: dict[str, Any]) -> bool:
    """คืน True ถ้าเป็น event ใหม่, False ถ้าซ้ำ (idempotent)."""
    ensure_tables()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO commerce_webhook_events(event_id,psp,type,payload_json,received_at) VALUES(?,?,?,?,?)"
            " ON CONFLICT(event_id) DO NOTHING",
            (event_id, psp, type, json.dumps(payload, ensure_ascii=False), utcnow()),
        )
        return cur.rowcount > 0


def seed_default_plans() -> list[dict[str, Any]]:
    plans = [
        {"id": "free", "name": "Free", "kind": "viewer", "price_thb": 0, "interval": "forever", "entitlements": ["catalog", "favorites"]},
        {"id": "creator", "name": "Creator", "kind": "creator", "price_thb": 19900, "interval": "monthly",
         "entitlements": ["catalog", "favorites", "submit_film", "creator_dashboard"]},
        {"id": "premium", "name": "Premium", "kind": "viewer", "price_thb": 12900, "interval": "monthly",
         "entitlements": ["catalog", "favorites", "early_access", "hd_streaming"]},
    ]
    return [upsert_plan(plan) for plan in plans]
