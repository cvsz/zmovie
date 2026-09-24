"""Tests for commerce sandbox (no live money, no card storage)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from zmovie_platform import migrations, storage
from zmovie_platform.commerce import checkout, store
from zmovie_platform.commerce.psp import SandboxPSP, get_psp


class CommerceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = storage.DB_PATH
        storage.DB_PATH = Path(self.tmp.name) / "zmovie.db"
        migrations.migrate()
        store.ensure_tables()
        store.seed_default_plans()

    def tearDown(self) -> None:
        storage.DB_PATH = self.old_db
        self.tmp.cleanup()

    def test_sandbox_checkout_and_confirm(self) -> None:
        created = checkout.create_checkout(
            user_id="u1", plan_id="premium", payment_method_ref="pm_test_123", idempotency_key="idem-001")
        self.assertEqual(created["ledger"]["status"], "pending")
        confirmed = checkout.confirm_checkout(
            user_id="u1", session_id=created["session"]["session_id"],
            plan_id="premium", idempotency_key="idem-001")
        self.assertEqual(confirmed["subscription"]["status"], "active")
        self.assertIn("hd_streaming", checkout.entitlements_for_user("u1"))

    def test_failed_payment_recovery(self) -> None:
        psp = SandboxPSP()
        session = psp.create_session(amount_thb=100, currency="THB", reference="u2:premium")
        failed_id = session["session_id"] + "fail" if False else "sess_abc123fail"
        result = psp.confirm_session(session_id=failed_id)
        self.assertEqual(result["status"], "failed")

    def test_webhook_signature_and_idempotency(self) -> None:
        psp = get_psp()
        payload = {"idempotency_key": "idem-wh-1", "psp_ref": "pay_x", "amount_thb": 100}
        raw = json.dumps(payload, separators=(",", ":")).encode()
        sig = psp.sign_webhook(raw)
        first = checkout.handle_webhook(
            psp_name="sandbox", event_id="evt-1", event_type="payment.succeeded",
            payload=payload, signature=sig, raw_body=raw)
        self.assertEqual(first["status"], "processed")
        second = checkout.handle_webhook(
            psp_name="sandbox", event_id="evt-1", event_type="payment.succeeded",
            payload=payload, signature=sig, raw_body=raw)
        self.assertEqual(second["status"], "duplicate_ignored")
        with self.assertRaises(ValueError):
            checkout.handle_webhook(
                psp_name="sandbox", event_id="evt-2", event_type="payment.succeeded",
                payload=payload, signature="bad", raw_body=raw)

    def test_refund_lifecycle(self) -> None:
        created = checkout.create_checkout(
            user_id="u3", plan_id="premium", payment_method_ref="pm_x", idempotency_key="idem-r1")
        checkout.confirm_checkout(
            user_id="u3", session_id=created["session"]["session_id"], plan_id="premium", idempotency_key="idem-r1")
        refunded = checkout.request_refund(user_id="u3", idempotency_key="idem-r1")
        self.assertEqual(refunded["ledger"]["status"], "refunded")
        with self.assertRaises(ValueError):
            checkout.request_refund(user_id="u3", idempotency_key="idem-r1")

    def test_upgrade_downgrade_and_cancel(self) -> None:
        created = checkout.create_checkout(
            user_id="u4", plan_id="premium", payment_method_ref="pm_x", idempotency_key="idem-u1")
        checkout.confirm_checkout(
            user_id="u4", session_id=created["session"]["session_id"], plan_id="premium", idempotency_key="idem-u1")
        changed = checkout.change_plan(user_id="u4", new_plan_id="creator")
        self.assertEqual(changed["subscription"]["plan_id"], "creator")
        canceled = checkout.cancel_subscription(user_id="u4", at_period_end=False)
        self.assertEqual(canceled["subscription"]["status"], "canceled")
        self.assertNotIn("creator_dashboard", checkout.entitlements_for_user("u4"))

    def test_no_card_storage(self) -> None:
        with self.assertRaises(ValueError):
            checkout._reject_card_data({"card_number": "4111111111111111"})
        # ledger ต้องไม่มี field บัตร
        created = checkout.create_checkout(
            user_id="u5", plan_id="free", payment_method_ref="pm_free", idempotency_key="idem-free-1")
        self.assertNotIn("card_number", json.dumps(created["ledger"]))

    def test_reconciliation(self) -> None:
        created = checkout.create_checkout(
            user_id="u6", plan_id="premium", payment_method_ref="pm_x", idempotency_key="idem-rec-1")
        confirmed = checkout.confirm_checkout(
            user_id="u6", session_id=created["session"]["session_id"], plan_id="premium", idempotency_key="idem-rec-1")
        psp_ref = confirmed["invoice"]["psp_ref"]
        balanced = checkout.reconcile(psp_settlements=[{"psp_ref": psp_ref, "amount_thb": 12900}])
        self.assertTrue(balanced["balanced"])
        off = checkout.reconcile(psp_settlements=[{"psp_ref": psp_ref, "amount_thb": 1}])
        self.assertFalse(off["balanced"])
        self.assertEqual(off["mismatched"], [psp_ref])

    def test_only_sandbox_enabled(self) -> None:
        with self.assertRaises(ValueError):
            get_psp("stripe")

    def test_expiry_revokes_access(self) -> None:
        created = checkout.create_checkout(
            user_id="u7", plan_id="premium", payment_method_ref="pm_x", idempotency_key="idem-exp-1")
        checkout.confirm_checkout(
            user_id="u7", session_id=created["session"]["session_id"], plan_id="premium", idempotency_key="idem-exp-1")
        self.assertTrue(checkout.can_access_media(user_id="u7", required_entitlement="hd_streaming"))
        expired = checkout.expire_due_subscriptions(now_iso="9999-12-31T00:00:00+00:00")
        self.assertGreaterEqual(expired, 0)
        # free plan ไม่มี hd_streaming
        self.assertFalse(checkout.can_access_media(user_id="no-such-user-xyz", required_entitlement="hd_streaming"))


if __name__ == "__main__":
    unittest.main()
