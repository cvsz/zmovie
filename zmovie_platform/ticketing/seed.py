"""Synthetic seed data (no live sales, sandbox only)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..models import utcnow
from ..storage import connect
from .store import ensure_tables


def seed_synthetic() -> dict[str, int]:
    """สร้างโรง/ห้อง/ผัง/หนัง/รอบฉายจำลองสำหรับทดสอบ."""
    ensure_tables()
    now = utcnow()
    base = datetime.now(timezone.utc).replace(microsecond=0)
    counts = {"branches": 0, "auditoriums": 0, "seats": 0, "movies": 0, "showtimes": 0}
    with connect() as conn:
        for branch_id, name, city in (("br-bkk", "ZeaZ Siam", "Bangkok"), ("br-cnx", "ZeaZ Maya", "Chiang Mai")):
            conn.execute(
                "INSERT INTO ticket_branches(id,name,city,active,created_at) VALUES(?,?,?,?,?)"
                " ON CONFLICT(id) DO NOTHING", (branch_id, name, city, 1, now))
            counts["branches"] += 1
        halls = (("ah-siam-1", "br-bkk", "Hall 1", 5, 8), ("ah-maya-1", "br-cnx", "Hall 1", 4, 6))
        for aud_id, branch_id, name, rows, cols in halls:
            conn.execute(
                "INSERT INTO ticket_auditoriums(id,branch_id,name,rows_count,cols_count,created_at) VALUES(?,?,?,?,?,?)"
                " ON CONFLICT(id) DO NOTHING", (aud_id, branch_id, name, rows, cols, now))
            counts["auditoriums"] += 1
            for r in range(rows):
                for c in range(cols):
                    seat_no = f"{chr(65 + r)}{c + 1:02d}"
                    kind = "accessible" if r == 0 and c < 2 else ("premium" if r < 2 else "standard")
                    conn.execute(
                        "INSERT INTO ticket_seats(auditorium_id,seat_no,kind,active) VALUES(?,?,?,1)"
                        " ON CONFLICT(auditorium_id,seat_no) DO NOTHING", (aud_id, seat_no, kind))
                    counts["seats"] += 1
        for movie_id, title, runtime, rating in (
            ("mv-neon", "Neon Harvest", 110, "13+"), ("mv-monsoon", "Monsoon Code", 95, "G")):
            conn.execute(
                "INSERT INTO ticket_movies(id,title,runtime_min,age_rating,created_at) VALUES(?,?,?,?,?)"
                " ON CONFLICT(id) DO NOTHING", (movie_id, title, runtime, rating, now))
            counts["movies"] += 1
        shows = (
            ("st-neon-1", "br-bkk", "ah-siam-1", "mv-neon", base + timedelta(hours=2), 220),
            ("st-monsoon-1", "br-cnx", "ah-maya-1", "mv-monsoon", base + timedelta(hours=3), 180),
        )
        for show_id, branch_id, aud_id, movie_id, starts, price in shows:
            conn.execute(
                "INSERT INTO ticket_showtimes(id,branch_id,auditorium_id,movie_id,starts_at,price_thb,status,created_at)"
                " VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING",
                (show_id, branch_id, aud_id, movie_id, starts.isoformat(), price, "scheduled", now))
            counts["showtimes"] += 1
    return counts
