"""Ticketing persistence: branches, auditoriums, seats, showtimes, holds, reservations, tickets, audit.

Concurrency safety:
- reservations has UNIQUE(showtime_id, seat_no) so double-selling is
  rejected by the database, not just application logic.
- hold/reserve use BEGIN IMMEDIATE transactions.
- SQLite is the local/test backend; schema is PostgreSQL-compatible
  (port by swapping the connection layer; see services/cinema-api/README).
"""
from __future__ import annotations

import json
import sqlite3
import time
from typing import Any

from ..models import utcnow
from ..storage import connect

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ticket_branches (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT NOT NULL DEFAULT '',
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ticket_auditoriums (
  id TEXT PRIMARY KEY,
  branch_id TEXT NOT NULL REFERENCES ticket_branches(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  rows_count INTEGER NOT NULL,
  cols_count INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ticket_seats (
  auditorium_id TEXT NOT NULL REFERENCES ticket_auditoriums(id) ON DELETE CASCADE,
  seat_no TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'standard',
  active INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (auditorium_id, seat_no)
);
CREATE TABLE IF NOT EXISTS ticket_movies (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  runtime_min INTEGER NOT NULL DEFAULT 90,
  age_rating TEXT NOT NULL DEFAULT 'G',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ticket_showtimes (
  id TEXT PRIMARY KEY,
  branch_id TEXT NOT NULL REFERENCES ticket_branches(id),
  auditorium_id TEXT NOT NULL REFERENCES ticket_auditoriums(id),
  movie_id TEXT NOT NULL REFERENCES ticket_movies(id),
  starts_at TEXT NOT NULL,
  price_thb INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'scheduled',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ticket_holds (
  id TEXT PRIMARY KEY,
  showtime_id TEXT NOT NULL REFERENCES ticket_showtimes(id) ON DELETE CASCADE,
  seat_no TEXT NOT NULL,
  holder_ref TEXT NOT NULL,
  idempotency_key TEXT UNIQUE NOT NULL,
  expires_at TEXT NOT NULL,
  consumed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ticket_reservations (
  id TEXT PRIMARY KEY,
  showtime_id TEXT NOT NULL REFERENCES ticket_showtimes(id) ON DELETE CASCADE,
  seat_no TEXT NOT NULL,
  holder_ref TEXT NOT NULL,
  hold_id TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'confirmed',
  idempotency_key TEXT UNIQUE NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(showtime_id, seat_no)
);
CREATE TABLE IF NOT EXISTS ticket_tickets (
  id TEXT PRIMARY KEY,
  reservation_id TEXT NOT NULL REFERENCES ticket_reservations(id) ON DELETE CASCADE,
  qr_payload TEXT NOT NULL,
  qr_signature TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'issued',
  checked_in_at TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ticket_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  event TEXT NOT NULL,
  actor TEXT NOT NULL DEFAULT '',
  details_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_ticket_holds_show ON ticket_holds(showtime_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_ticket_res_show ON ticket_reservations(showtime_id, status);
"""


def ensure_tables() -> None:
    with connect() as conn:
        conn.executescript(TABLE_SQL)


def audit(event: str, actor: str = "", **details: Any) -> None:
    ensure_tables()
    payload = json.dumps(details, ensure_ascii=False)
    # retry เมื่อเจอ database-is-locked ภายใต้ concurrency test
    last_exc: Exception | None = None
    for attempt in range(8):
        try:
            with connect() as conn:
                conn.execute(
                    "INSERT INTO ticket_audit(ts,event,actor,details_json) VALUES(?,?,?,?)",
                    (utcnow(), event, actor, payload),
                )
            return
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower():
                raise
            last_exc = exc
            time.sleep(0.05 * (2**attempt))
    if last_exc is not None:
        raise last_exc


def _row(conn: Any, query: str, params: tuple = ()) -> dict[str, Any] | None:
    row = conn.execute(query, params).fetchone()
    return dict(row) if row else None
