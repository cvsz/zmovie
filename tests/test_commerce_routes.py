"""Tests for commerce HTTP boundary (sandbox, auth-gated)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from zmovie_platform import auth, migrations, storage
from zmovie_platform.commerce.store import seed_default_plans


def _client():
    import main

    return TestClient(main.app)


class CommerceRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.old_db = storage.DB_PATH
        storage.DB_PATH = Path(cls.tmp.name) / "zmovie.db"
        migrations.migrate()
        seed_default_plans()
        auth.create_user("buyer1", "buyer1-password-long", "user")
        cls.token = auth.issue_token({"username": "buyer1", "role": "user"})

    @classmethod
    def tearDownClass(cls) -> None:
        storage.DB_PATH = cls.old_db
        cls.tmp.cleanup()

    def setUp(self) -> None:
        self.client = _client()
        self.auth = {"Authorization": f"Bearer {self.token}"}

    def test_plans_public(self) -> None:
        resp = self.client.get("/api/v2/commerce/plans")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["sandbox"])
        self.assertGreaterEqual(len(resp.json()["items"]), 3)

    def test_subscription_requires_auth(self) -> None:
        self.assertEqual(self.client.get("/api/v2/commerce/subscription").status_code, 401)

    def test_full_sandbox_flow(self) -> None:
        key = "idem-route-001"
        created = self.client.post("/api/v2/commerce/checkout", headers=self.auth, json={
            "plan_id": "premium", "payment_method_ref": "pm_route_test", "idempotency_key": key})
        self.assertEqual(created.status_code, 200)
        session_id = created.json()["session"]["session_id"]
        confirmed = self.client.post("/api/v2/commerce/checkout/confirm", headers=self.auth, json={
            "session_id": session_id, "plan_id": "premium", "idempotency_key": key})
        self.assertEqual(confirmed.status_code, 200)
        sub = self.client.get("/api/v2/commerce/subscription", headers=self.auth).json()
        self.assertEqual(sub["subscription"]["status"], "active")
        self.assertIn("hd_streaming", sub["entitlements"])
        ledger = self.client.get("/api/v2/commerce/ledger", headers=self.auth).json()
        self.assertTrue(any(e["idempotency_key"] == key for e in ledger["items"]))
        canceled = self.client.post("/api/v2/commerce/subscription/cancel", headers=self.auth)
        self.assertEqual(canceled.status_code, 200)

    def test_card_data_rejected_at_boundary(self) -> None:
        resp = self.client.post("/api/v2/commerce/checkout", headers=self.auth, json={
            "plan_id": "premium", "payment_method_ref": "pm_x", "idempotency_key": "idem-card-1",
            "card_number": "4111111111111111"})
        self.assertEqual(resp.status_code, 400)

    def test_bad_method_ref_rejected(self) -> None:
        resp = self.client.post("/api/v2/commerce/checkout", headers=self.auth, json={
            "plan_id": "premium", "payment_method_ref": "4111111111111111", "idempotency_key": "idem-card-2"})
        self.assertEqual(resp.status_code, 400)

    def test_webhook_bad_signature_rejected(self) -> None:
        resp = self.client.post("/api/v2/commerce/webhooks", json={
            "psp_name": "sandbox", "event_id": "e1", "event_type": "payment.succeeded",
            "payload": {}, "signature": "bad"})
        self.assertEqual(resp.status_code, 400)

    def test_membership_page_served(self) -> None:
        resp = self.client.get("/membership")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Sandbox", resp.text)


if __name__ == "__main__":
    unittest.main()
