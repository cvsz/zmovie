"""Cinema ticketing service (separate commerce domain).

Thin FastAPI layer over zmovie_platform.ticketing core.
Binds to 127.0.0.1 by default; front behind Cloudflare Tunnel +
existing auth in production. No live ticket sales without payment,
refund, legal and operational acceptance.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from zmovie_platform.migrations import migrate
from zmovie_platform.ticketing import booking
from zmovie_platform.ticketing.seed import seed_synthetic
from zmovie_platform.ticketing.store import ensure_tables

migrate()
ensure_tables()

app = FastAPI(title="ZeaZ Cinema Ticketing API", version="0.1.0")


def _admin(required: str | None = Header(default=None, alias="X-Cinema-Admin-Token")) -> None:
    expected = os.getenv("CINEMA_ADMIN_TOKEN", "")
    if not expected or required != expected:
        raise HTTPException(status_code=401, detail="invalid cinema admin token")


class HoldRequest(BaseModel):
    showtime_id: str = Field(min_length=1, max_length=200)
    seat_no: str = Field(min_length=2, max_length=10)
    holder_ref: str = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=8, max_length=128)


class ConfirmRequest(BaseModel):
    hold_id: str = Field(min_length=1, max_length=200)
    holder_ref: str = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=8, max_length=128)


class CancelRequest(BaseModel):
    reservation_id: str = Field(min_length=1, max_length=200)
    holder_ref: str = Field(min_length=1, max_length=200)


class CheckinRequest(BaseModel):
    qr_payload: str = Field(min_length=8)
    qr_signature: str = Field(min_length=8)


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "healthy", "service": "cinema-ticketing", "synthetic": True}


@app.post("/admin/seed")
def admin_seed(_: None = Header(default=None, alias="X-Cinema-Admin-Token")) -> dict[str, object]:
    _admin(_)
    return {"seeded": seed_synthetic()}


@app.get("/showtimes/{showtime_id}/availability")
def show_availability(showtime_id: str) -> dict[str, object]:
    try:
        return booking.availability(showtime_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/holds")
def create_hold(payload: HoldRequest) -> dict[str, object]:
    try:
        return booking.hold_seat(
            showtime_id=payload.showtime_id, seat_no=payload.seat_no,
            holder_ref=payload.holder_ref, idempotency_key=payload.idempotency_key)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/reservations/confirm")
def confirm(payload: ConfirmRequest) -> dict[str, object]:
    try:
        return booking.confirm_hold(
            hold_id=payload.hold_id, holder_ref=payload.holder_ref, idempotency_key=payload.idempotency_key)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/reservations/cancel")
def cancel(payload: CancelRequest) -> dict[str, object]:
    try:
        return booking.cancel_reservation(reservation_id=payload.reservation_id, holder_ref=payload.holder_ref)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/tickets/check-in")
def checkin(payload: CheckinRequest) -> dict[str, object]:
    try:
        return booking.check_in(qr_payload=payload.qr_payload, qr_signature=payload.qr_signature, actor="counter")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/holds/sweep")
def sweep(_: None = Header(default=None, alias="X-Cinema-Admin-Token")) -> dict[str, object]:
    _admin(_)
    return {"released": booking.release_expired_holds()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8095)
