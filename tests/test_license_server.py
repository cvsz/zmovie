"""Contract tests for the versioned License Server (ephemeral keys only)."""
from __future__ import annotations

import base64
import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


def _load_app():
    service_dir = str(Path(__file__).resolve().parent.parent / "services" / "license-server")
    sys.path.insert(0, service_dir)
    os.environ["LICENSE_KEYS_DIR"] = tempfile.mkdtemp(prefix="lic-test-")
    os.environ["LICENSE_SEED_KEYS"] = "test-key-001"
    os.environ["LICENSE_ADMIN_TOKEN"] = "test-admin-token"
    os.environ["LICENSE_RATE_LIMIT_MAX"] = "1000"
    import server as license_server

    importlib.reload(license_server)
    return license_server


def _b64url(data: dict) -> str:
    raw = json.dumps(data, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


class LicenseServerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_app()
        from fastapi.testclient import TestClient

        cls.client = TestClient(cls.mod.app)

    def test_activate_issues_three_part_lease(self) -> None:
        resp = self.client.post("/v1/activate", json={
            "key": "test-key-001", "product": "zmovie", "site_url": "https://zmovie.zeaz.dev"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["lease"].split(".")), 3)

    def test_wrong_product_and_site_rejected(self) -> None:
        for body in ({"key": "test-key-001", "product": "other", "site_url": "https://zmovie.zeaz.dev"},
                     {"key": "test-key-001", "product": "zmovie", "site_url": "https://evil.example"}):
            self.assertEqual(self.client.post("/v1/activate", json=body).status_code, 422)

    def test_unknown_key_rejected(self) -> None:
        resp = self.client.post("/v1/activate", json={
            "key": "nope", "product": "zmovie", "site_url": "https://zmovie.zeaz.dev"})
        self.assertEqual(resp.status_code, 404)

    def test_admin_endpoints_gated(self) -> None:
        self.assertEqual(self.client.get("/v1/leases/abcdef123456").status_code, 401)
        self.assertEqual(self.client.post("/v1/admin/revoke", json={"key": "valid-key-1"}).status_code, 401)

    def test_revoke_and_expire_fail_closed(self) -> None:
        admin = {"X-License-Admin-Token": "test-admin-token"}
        self.assertEqual(
            self.client.post("/v1/admin/revoke", json={"key": "rev-key-001"}, headers=admin).status_code, 200)
        os.environ["LICENSE_SEED_KEYS"] = "rev-key-001"
        importlib.reload(self.mod)
        from fastapi.testclient import TestClient

        client = TestClient(self.mod.app)
        self.assertEqual(client.post("/v1/admin/revoke", json={"key": "rev-key-001"}, headers=admin).status_code, 200)
        resp = client.post("/v1/activate", json={
            "key": "rev-key-001", "product": "zmovie", "site_url": "https://zmovie.zeaz.dev"})
        self.assertEqual(resp.status_code, 404)

    def test_tampered_lease_structure(self) -> None:
        os.environ["LICENSE_SEED_KEYS"] = "test-key-001"
        importlib.reload(self.mod)
        from fastapi.testclient import TestClient

        client = TestClient(self.mod.app)
        resp = client.post("/v1/activate", json={
            "key": "test-key-001", "product": "zmovie", "site_url": "https://zmovie.zeaz.dev"})
        header_b64, claims_b64, sig_b64 = resp.json()["lease"].split(".")
        claims = json.loads(base64.urlsafe_b64decode(claims_b64 + "=" * (-len(claims_b64) % 4)))
        self.assertEqual(claims["iss"], "zeaz-license")
        self.assertEqual(claims["aud"], "zmovie")
        self.assertLessEqual(claims["exp"] - claims["iat"], 900)
        self.assertIn("cinema.creator", claims["features"])

    def test_public_key_matches_signer(self) -> None:
        from cryptography.hazmat.primitives import serialization

        pub = self.client.get("/v1/public-key").json()["public_key"]
        raw = self.mod.public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.assertEqual(pub, base64.urlsafe_b64encode(raw).decode().rstrip("="))


if __name__ == "__main__":
    unittest.main()
