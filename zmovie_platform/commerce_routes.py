"""Membership/commerce HTTP boundary (sandbox only, no live money)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError

from .api_routes import current_actor
from .audit import write as audit
from .commerce import checkout
from .commerce.checkout import _reject_card_data
from .commerce.store import ledger_for_user, list_plans

router = APIRouter(prefix="/api/v2/commerce")


class CheckoutRequest(BaseModel):
    plan_id: str = Field(min_length=1, max_length=100)
    payment_method_ref: str = Field(min_length=4, max_length=200)
    idempotency_key: str = Field(min_length=8, max_length=128)


class ConfirmRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=200)
    plan_id: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=8, max_length=128)


class PlanChangeRequest(BaseModel):
    new_plan_id: str = Field(min_length=1, max_length=100)


class RefundRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=128)


class WebhookRequest(BaseModel):
    psp_name: str = Field(default="sandbox", max_length=40)
    event_id: str = Field(min_length=1, max_length=200)
    event_type: str = Field(min_length=1, max_length=100)
    payload: dict = Field(default_factory=dict)
    signature: str = Field(min_length=1, max_length=256)


def _user(actor: dict[str, str]) -> str:
    return str(actor.get("username", "unknown"))


@router.get("/plans", tags=["commerce"])
def plans() -> dict[str, object]:
    return {"items": list_plans(), "sandbox": True}


@router.get("/subscription", tags=["commerce"])
def my_subscription(actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    user_id = _user(actor)
    return {
        "subscription": checkout.store.active_subscription_for_user(user_id),
        "entitlements": checkout.entitlements_for_user(user_id),
        "sandbox": True,
    }


@router.get("/ledger", tags=["commerce"])
def my_ledger(actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    return {"items": ledger_for_user(_user(actor)), "sandbox": True}


@router.post("/checkout", tags=["commerce"])
async def create(request: Request, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    try:
        raw = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid JSON body") from exc
    if not isinstance(raw, dict):
        raise HTTPException(status_code=400, detail="invalid checkout body")
    try:
        _reject_card_data(raw)
    except ValueError as exc:
        audit("commerce.card_data_rejected", actor=_user(actor))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        payload = CheckoutRequest(**raw)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc.errors())) from exc
    try:
        result = checkout.create_checkout(
            user_id=_user(actor), plan_id=payload.plan_id,
            payment_method_ref=payload.payment_method_ref, idempotency_key=payload.idempotency_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {**result, "sandbox": True}


@router.post("/checkout/confirm", tags=["commerce"])
def confirm(payload: ConfirmRequest, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    try:
        result = checkout.confirm_checkout(
            user_id=_user(actor), session_id=payload.session_id,
            plan_id=payload.plan_id, idempotency_key=payload.idempotency_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {**result, "sandbox": True}


@router.post("/subscription/change", tags=["commerce"])
def change_plan(payload: PlanChangeRequest, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    try:
        return checkout.change_plan(user_id=_user(actor), new_plan_id=payload.new_plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/subscription/cancel", tags=["commerce"])
def cancel(actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    try:
        return checkout.cancel_subscription(user_id=_user(actor))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/refunds", tags=["commerce"])
def refund(payload: RefundRequest, actor: dict[str, str] = Depends(current_actor)) -> dict[str, object]:
    try:
        return checkout.request_refund(user_id=_user(actor), idempotency_key=payload.idempotency_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/webhooks", tags=["commerce"])
async def webhooks(payload: WebhookRequest, request: Request) -> dict[str, object]:
    body = await request.body()
    try:
        return checkout.handle_webhook(
            psp_name=payload.psp_name, event_id=payload.event_id, event_type=payload.event_type,
            payload=payload.payload, signature=payload.signature, raw_body=body)
    except ValueError as exc:
        audit("commerce.webhook.rejected", actor="psp")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
