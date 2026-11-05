from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from starlette.requests import Request

from zmovie_platform import api_routes, auth, oauth, storage


class OAuthSecurityTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db_path = storage.DB_PATH
        storage.DB_PATH = Path(self.tmp.name) / "zmovie.db"
        storage.ensure_database()
        oauth.ensure_oauth_tables()

    async def asyncTearDown(self) -> None:
        storage.DB_PATH = self.old_db_path
        self.tmp.cleanup()

    async def _create_existing_user(self, username: str, email: str) -> dict[str, object]:
        user = auth.create_user(username, "correct-horse", "admin")
        with storage.connect() as conn:
            conn.execute("UPDATE users SET email=? WHERE id=?", (email, user["id"]))
        return user

    async def test_unverified_email_does_not_link_existing_account(self) -> None:
        existing = await self._create_existing_user("owner", "owner@example.com")
        user = await oauth.find_or_create_oauth_user(
            "google",
            {"sub": "external-123", "email": "owner@example.com", "email_verified": False},
        )
        self.assertNotEqual(user["id"], existing["id"])
        self.assertEqual(user["role"], "user")
        self.assertTrue(str(user["username"]).startswith("google_external"))
        with storage.connect() as conn:
            saved = conn.execute("SELECT email FROM users WHERE id=?", (user["id"],)).fetchone()
            linked = conn.execute("SELECT user_id FROM oauth_links WHERE provider_sub=?", ("external-123",)).fetchone()
        self.assertEqual(saved["email"], "")
        self.assertEqual(linked["user_id"], user["id"])

    async def test_verified_email_can_link_matching_existing_account(self) -> None:
        existing = await self._create_existing_user("owner", "Owner@Example.com")
        user = await oauth.find_or_create_oauth_user(
            "google",
            {"sub": "verified-123", "email": "owner@example.com", "email_verified": True},
        )
        self.assertEqual(user["id"], existing["id"])
        self.assertEqual(user["role"], "admin")

    async def test_oauth_callback_redirects_token_to_studio_fragment(self) -> None:
        state = "state-value"
        token = "signed.api.token"
        manager = SimpleNamespace(
            _state_store={state: ("google", "verifier", time.time() + 600, None)},
            exchange_code_for_provider=AsyncMock(return_value={"userinfo": {"sub": "user-1"}}),
        )
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "scheme": "https",
                "path": "/api/v2/auth/oauth/callback",
                "raw_path": b"/api/v2/auth/oauth/callback",
                "query_string": b"",
                "headers": [(b"cookie", f"oauth_state={state}".encode())],
                "client": ("127.0.0.1", 12345),
                "server": ("app.example", 443),
            }
        )
        config = SimpleNamespace(auth_enabled=True, oauth_enabled=True, base_url="https://app.example")
        with patch.object(api_routes, "settings", config), patch.object(
            api_routes, "get_oauth_manager", return_value=manager
        ), patch.object(api_routes, "find_or_create_oauth_user", new=AsyncMock(return_value={"username": "owner"})), patch.object(
            api_routes, "issue_token", return_value=token
        ), patch.object(api_routes, "audit"):
            response = await api_routes.oauth_callback(request, code="authorization-code", state=state)

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], f"https://app.example/studio#oauth_token={token}")
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")
        self.assertNotIn(token, response.body.decode())
        manager.exchange_code_for_provider.assert_awaited_once()

    async def test_public_oauth_rejects_unconfigured_host_header(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "scheme": "https",
                "path": "/api/v2/auth/oauth/login/google",
                "raw_path": b"/api/v2/auth/oauth/login/google",
                "query_string": b"",
                "headers": [(b"host", b"attacker.example")],
                "client": ("127.0.0.1", 12345),
                "server": ("attacker.example", 443),
            }
        )
        with patch.object(api_routes, "settings", SimpleNamespace(base_url="")):
            with self.assertRaises(api_routes.HTTPException) as denied:
                api_routes.oauth_base_url(request)
        self.assertEqual(denied.exception.status_code, 503)

    async def test_loopback_host_header_from_remote_peer_is_rejected(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "scheme": "http",
                "path": "/api/v2/auth/oauth/login/google",
                "raw_path": b"/api/v2/auth/oauth/login/google",
                "query_string": b"",
                "headers": [(b"host", b"127.0.0.1:8080")],
                "client": ("203.0.113.12", 12345),
                "server": ("127.0.0.1", 8080),
            }
        )
        with patch.object(api_routes, "settings", SimpleNamespace(base_url="")):
            with self.assertRaises(api_routes.HTTPException) as denied:
                api_routes.oauth_base_url(request)
        self.assertEqual(denied.exception.status_code, 503)

    async def test_loopback_oauth_can_use_local_request_origin(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "scheme": "http",
                "path": "/api/v2/auth/oauth/login/google",
                "raw_path": b"/api/v2/auth/oauth/login/google",
                "query_string": b"",
                "headers": [(b"host", b"127.0.0.1:8080")],
                "client": ("127.0.0.1", 12345),
                "server": ("127.0.0.1", 8080),
            }
        )
        with patch.object(api_routes, "settings", SimpleNamespace(base_url="")):
            self.assertEqual(api_routes.oauth_base_url(request), "http://127.0.0.1:8080")


if __name__ == "__main__":
    unittest.main()
