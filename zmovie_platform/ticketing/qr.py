"""Signed QR tickets (HMAC-SHA256, short payload, offline verifiable)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time


def _secret() -> bytes:
    return os.getenv("CINEMA_QR_SECRET", "cinema-qr-dev-secret").encode("utf-8")


def issue_qr(*, ticket_id: str, showtime_id: str, seat_no: str, ttl_seconds: int = 86400) -> dict[str, str]:
    payload = {
        "ticket_id": ticket_id,
        "showtime_id": showtime_id,
        "seat_no": seat_no,
        "exp": int(time.time()) + ttl_seconds,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    body = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
    sig = hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest()
    return {"qr_payload": body, "qr_signature": sig}


def verify_qr(*, qr_payload: str, qr_signature: str) -> dict | None:
    try:
        expected = hmac.new(_secret(), qr_payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, qr_signature or ""):
            return None
        raw = base64.urlsafe_b64decode(qr_payload + "=" * (-len(qr_payload) % 4))
        payload = json.loads(raw.decode())
        if not isinstance(payload, dict) or int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
