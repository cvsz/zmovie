"""PSP abstraction + sandbox implementation (no real money, no card storage)."""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any


class BasePSP:
    name = "base"

    def create_session(self, *, amount_thb: int, currency: str, reference: str) -> dict[str, Any]:
        raise NotImplementedError

    def confirm_session(self, *, session_id: str) -> dict[str, Any]:
        raise NotImplementedError

    def refund(self, *, psp_ref: str, amount_thb: int) -> dict[str, Any]:
        raise NotImplementedError

    def sign_webhook(self, payload: bytes) -> str:
        raise NotImplementedError

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        raise NotImplementedError


def _webhook_secret() -> bytes:
    return os.getenv("ZMOVIE_PSP_WEBHOOK_SECRET", "sandbox-webhook-secret").encode("utf-8")


class SandboxPSP(BasePSP):
    """PSP จำลองสำหรับทดสอบ: ไม่แตะเงินจริง ไม่เก็บบัตร."""

    name = "sandbox"

    def create_session(self, *, amount_thb: int, currency: str, reference: str) -> dict[str, Any]:
        if amount_thb < 0:
            raise ValueError("amount must be >= 0")
        digest = hashlib.sha256(f"{reference}:{amount_thb}:{time.time_ns()}".encode()).hexdigest()[:24]
        return {
            "session_id": f"sess_{digest}",
            "psp": self.name,
            "amount_thb": amount_thb,
            "currency": currency,
            "reference": reference,
            "checkout_url": f"https://sandbox-pay.example/checkout/sess_{digest}",
            "status": "requires_confirmation",
        }

    def confirm_session(self, *, session_id: str) -> dict[str, Any]:
        if not session_id.startswith("sess_"):
            raise ValueError("unknown session")
        # sandbox: session ที่ลงท้ายด้วย 'fail' ถือว่าชำระไม่สำเร็จ (ทดสอบ failure recovery)
        if session_id.endswith("fail"):
            return {"session_id": session_id, "status": "failed", "psp_ref": f"pay_{session_id[5:]}"}
        return {"session_id": session_id, "status": "succeeded", "psp_ref": f"pay_{session_id[5:]}"}

    def refund(self, *, psp_ref: str, amount_thb: int) -> dict[str, Any]:
        if not psp_ref.startswith("pay_"):
            raise ValueError("unknown payment")
        return {"psp_ref": psp_ref, "status": "refunded", "amount_thb": amount_thb}

    def sign_webhook(self, payload: bytes) -> str:
        return hmac.new(_webhook_secret(), payload, hashlib.sha256).hexdigest()

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        expected = self.sign_webhook(payload)
        return hmac.compare_digest(expected, signature or "")


def get_psp(name: str | None = None) -> BasePSP:
    selected = (name or os.getenv("ZMOVIE_PSP", "sandbox")).strip().lower()
    if selected != "sandbox":
        # ปิดกั้น PSP จริงจนกว่าจะมี approved secret-management workflow
        raise ValueError("only sandbox PSP is enabled (live payments require explicit operator approval)")
    return SandboxPSP()
