"""Cross-cutting security regression tests (auth domains, injection, replay)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from zmovie_platform import auth, migrations, privacy, storage
from zmovie_platform.commerce import checkout
from zmovie_platform.commerce import store as commerce_store
from zmovie_platform.commerce.psp import get_psp
from zmovie_platform.security import safe_project_path, validate_managed_asset_path
from zmovie_platform.ticketing.qr import issue_qr, verify_qr


class SecurityRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = storage.DB_PATH
        storage.DB_PATH = Path(self.tmp.name) / "zmovie.db"
        migrations.migrate()
        commerce_store.ensure_tables()
        commerce_store.seed_default_plans()

    def tearDown(self) -> None:
        storage.DB_PATH = self.old_db
        self.tmp.cleanup()

    def test_service_token_rejects_api_jwt(self) -> None:
        from zmovie_platform import studio_cinema

        token = auth.issue_token({"username": "admin", "role": "admin"})
        self.assertFalse(studio_cinema.verify_service_token(token))
        self.assertFalse(studio_cinema.verify_service_token("Bearer " + token))

    def test_ssrf_paths_rejected(self) -> None:
        for evil in ("/etc/passwd", "https://evil.example/x.mp4", "../../etc/shadow", "", "   "):
            with self.assertRaises(ValueError, msg=evil):
                validate_managed_asset_path(evil)

    def test_upload_traversal_rejected(self) -> None:
        root = Path(self.tmp.name)
        # filename traversal ถูก neutralize เป็น basename ภายใต้ project dir
        neutralized = safe_project_path(root, "prj1", "../../evil.mp4")
        self.assertEqual(neutralized, (root / "prj1" / "evil.mp4").resolve())
        with self.assertRaises(ValueError):
            safe_project_path(root, "../..", "x.mp4")

    def test_sqli_attempt_is_inert(self) -> None:
        # parameterized queries: malicious input must not leak or crash
        with storage.connect() as conn:
            rows = conn.execute("SELECT * FROM projects WHERE owner=?", ("' OR '1'='1",)).fetchall()
        self.assertEqual(list(rows), [])

    def test_webhook_replay_and_tamper(self) -> None:
        psp = get_psp()
        payload = {"idempotency_key": "sec-1", "psp_ref": "pay_a", "amount_thb": 10}
        raw = json.dumps(payload, separators=(",", ":")).encode()
        sig = psp.sign_webhook(raw)
        first = checkout.handle_webhook(
            psp_name="sandbox", event_id="sec-evt-1", event_type="payment.succeeded",
            payload=payload, signature=sig, raw_body=raw)
        self.assertEqual(first["status"], "processed")
        dup = checkout.handle_webhook(
            psp_name="sandbox", event_id="sec-evt-1", event_type="payment.succeeded",
            payload=payload, signature=sig, raw_body=raw)
        self.assertEqual(dup["status"], "duplicate_ignored")
        tampered = raw + b" "
        with self.assertRaises(ValueError):
            checkout.handle_webhook(
                psp_name="sandbox", event_id="sec-evt-2", event_type="payment.succeeded",
                payload=payload, signature=sig, raw_body=tampered)

    def test_qr_tamper_rejected(self) -> None:
        qr = issue_qr(ticket_id="t1", showtime_id="s1", seat_no="A01", ttl_seconds=3600)
        self.assertIsNotNone(verify_qr(qr_payload=qr["qr_payload"], qr_signature=qr["qr_signature"]))
        self.assertIsNone(verify_qr(qr_payload=qr["qr_payload"], qr_signature="0" * 64))
        self.assertIsNone(verify_qr(qr_payload="bogus", qr_signature=qr["qr_signature"]))

    def test_privacy_export_redacts_and_delete_requires_confirmation(self) -> None:
        auth.create_user("privacyuser", "supersecret-password", "user")
        export = privacy.export_user_data("privacyuser")
        self.assertEqual(export["user"]["password_hash"], "[REDACTED]")
        with self.assertRaises(ValueError):
            privacy.delete_user_data("privacyuser", confirmation="wrong")
        result = privacy.delete_user_data("privacyuser", confirmation="privacyuser")
        self.assertEqual(result["deleted_user"], "privacyuser")
        self.assertIsNone(auth.authenticate("privacyuser", "supersecret-password"))

    def test_passwords_hashed_not_plaintext(self) -> None:
        auth.create_user("hashuser", "another-secret-pw", "user")
        with storage.connect() as conn:
            row = conn.execute("SELECT password_hash FROM users WHERE username=?", ("hashuser",)).fetchone()
        self.assertIsNotNone(row)
        self.assertNotIn("another-secret-pw", row["password_hash"])
        self.assertTrue(row["password_hash"].startswith("pbkdf2_sha256$"))


if __name__ == "__main__":
    unittest.main()
