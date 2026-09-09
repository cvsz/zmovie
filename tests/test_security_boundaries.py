from __future__ import annotations

import os
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

import app
from zmovie_platform import api_routes, auth, health, publisher_routes, storage
from zmovie_platform.api_schemas import AssetRequest, BootstrapRequest, LoginRequest


def request_from_host(host: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [],
            "client": (host, 12345),
            "server": ("testserver", 80),
        }
    )


class SecurityBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_storage_db = storage.DB_PATH
        storage.DB_PATH = self.root / "zmovie.db"
        storage.ensure_database()

    def tearDown(self) -> None:
        storage.DB_PATH = self.old_storage_db
        self.tmp.cleanup()

    def test_legacy_state_endpoints_require_admin_when_auth_enabled(self) -> None:
        with patch("app.settings", SimpleNamespace(auth_enabled=True)):
            with self.assertRaises(HTTPException) as missing:
                app.legacy_admin(None)
            self.assertEqual(missing.exception.status_code, 401)

            user_token = auth.issue_token({"username": "editor", "role": "user"})
            with self.assertRaises(HTTPException) as forbidden:
                app.legacy_admin(f"Bearer {user_token}")
            self.assertEqual(forbidden.exception.status_code, 403)

            admin_token = auth.issue_token({"username": "admin", "role": "admin"})
            self.assertEqual(
                app.legacy_admin(f"Bearer {admin_token}")["role"],
                "admin",
            )

    def test_legacy_function_calls_remain_compatible(self) -> None:
        request = app.GenerateRequest(count=1, seed=42, save_history=False)
        self.assertEqual(app.generate(request)["count"], 1)

    def test_login_is_rate_limited_per_client(self) -> None:
        host = f"198.51.100.{uuid.uuid4().int % 200 + 1}"
        request = request_from_host(host)
        with patch.object(api_routes, "authenticate", return_value=None), patch.object(api_routes, "increment"):
            for _ in range(10):
                with self.assertRaises(HTTPException) as failed:
                    api_routes.login(LoginRequest(username="admin", password="wrong"), request)
                self.assertEqual(failed.exception.status_code, 401)
            with self.assertRaises(HTTPException) as limited:
                api_routes.login(LoginRequest(username="admin", password="wrong"), request)
        self.assertEqual(limited.exception.status_code, 429)
        self.assertEqual(limited.exception.headers["Retry-After"], "60")

    def test_bootstrap_is_rate_limited_per_client(self) -> None:
        host = f"203.0.113.{uuid.uuid4().int % 200 + 1}"
        request = request_from_host(host)
        payload = BootstrapRequest(username="admin", password="correct-horse")
        user = {"id": 1, "username": "admin", "role": "admin"}
        with patch.object(api_routes, "user_count", return_value=0), patch.object(
            api_routes, "create_user", return_value=user
        ), patch.object(api_routes, "issue_token", return_value="token"), patch.object(api_routes, "audit"):
            for _ in range(5):
                self.assertEqual(api_routes.bootstrap(payload, request)["token"], "token")
            with self.assertRaises(HTTPException) as limited:
                api_routes.bootstrap(payload, request)
        self.assertEqual(limited.exception.status_code, 429)

    def test_legacy_generation_is_rate_limited(self) -> None:
        host = f"192.0.2.{uuid.uuid4().int % 200 + 1}"
        request = request_from_host(host)
        for _ in range(30):
            app.legacy_generate_rate_limit(request)
        with self.assertRaises(HTTPException) as limited:
            app.legacy_generate_rate_limit(request)
        self.assertEqual(limited.exception.status_code, 429)

    def test_public_health_projection_omits_server_details(self) -> None:
        report = health.public_health_report(
            {
                "status": "ok",
                "database": "/var/lib/zmovie/zmovie.db",
                "database_exists": True,
                "media_root": "/var/lib/zmovie/media",
                "ffmpeg": True,
                "ffprobe": True,
                "paths": {"media": {"path": "/var/lib/zmovie/media", "writable": True}},
                "comfyui": {
                    "configured": True,
                    "reachable": True,
                    "workflow_valid": True,
                    "nodes_available": True,
                    "ready": True,
                    "accelerated": False,
                    "workflow_role": "smoke",
                    "url": "http://127.0.0.1:8188",
                    "workflow": "/var/lib/zmovie/workflow.json",
                    "probe_error": "internal detail",
                },
                "render_ready": True,
                "production_video_ready": False,
            }
        )
        self.assertEqual(report["status"], "ok")
        self.assertTrue(report["render_ready"])
        self.assertNotIn("database", report)
        self.assertNotIn("media_root", report)
        self.assertNotIn("paths", report)
        self.assertNotIn("url", report["comfyui"])
        self.assertNotIn("workflow", report["comfyui"])
        self.assertNotIn("probe_error", report["comfyui"])

    def test_asset_registration_rejects_unmanaged_and_symlink_escape_paths(self) -> None:
        media_root = self.root / "media"
        media_root.mkdir()
        outside = self.root / "outside.mp4"
        outside.write_bytes(b"not a real video")
        symlink = media_root / "escape.mp4"
        symlink.symlink_to(outside)
        valid = media_root / "project" / "clip.mp4"

        payload = AssetRequest(kind="render", name="clip", path=str(valid))
        with patch.dict(os.environ, {"ZMOVIE_MEDIA_ROOT": str(media_root)}, clear=False), patch.object(
            api_routes, "require_project", return_value=object()
        ), patch.object(api_routes, "add_asset", return_value={"id": "asset-1", "path": str(valid)}) as add_asset:
            result = api_routes.create_asset("prj_test", payload, actor={"username": "admin", "role": "admin"})
            self.assertEqual(result["id"], "asset-1")
            add_asset.assert_called_once_with("prj_test", "render", "clip", str(valid.resolve()))

            with self.assertRaises(HTTPException) as outside_error:
                api_routes.create_asset(
                    "prj_test",
                    payload.model_copy(update={"path": str(outside)}),
                    actor={"username": "admin", "role": "admin"},
                )
            self.assertEqual(outside_error.exception.status_code, 400)

            with self.assertRaises(HTTPException) as symlink_error:
                api_routes.create_asset(
                    "prj_test",
                    payload.model_copy(update={"path": str(symlink)}),
                    actor={"username": "admin", "role": "admin"},
                )
            self.assertEqual(symlink_error.exception.status_code, 400)

    def test_public_publisher_job_serializer_excludes_local_paths(self) -> None:
        job = {
            "id": "pub_123",
            "project_id": "prj_123",
            "status": "prepared",
            "title": "A zMovie",
            "video_path": "/var/lib/zmovie/media/movie.mp4",
            "cover_path": "/var/lib/zmovie/publish/cover.jpg",
            "subtitle_path": "/var/lib/zmovie/publish/subtitles.srt",
            "state_path": "/var/lib/zmovie/bilibili/storage_state.json",
            "metadata": {"approval_required": True},
        }
        public = publisher_routes._public_publish_job(job)
        self.assertEqual(public["id"], "pub_123")
        for field in ("video_path", "cover_path", "subtitle_path", "state_path"):
            self.assertNotIn(field, public)

    def test_unset_secret_does_not_use_source_controlled_fallback(self) -> None:
        with patch.dict(os.environ, {"ZMOVIE_SECRET_KEY": ""}, clear=False):
            self.assertNotEqual(auth._secret(), b"zmovie-local-development-secret-change-me")
            token = auth.issue_token({"username": "admin", "role": "admin"})
            self.assertIsNotNone(auth.decode_token(token))


if __name__ == "__main__":
    unittest.main()
