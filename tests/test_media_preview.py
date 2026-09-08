from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi import HTTPException

from zmovie_platform import auth, storage
from zmovie_platform.media_preview import _asset_for_preview, stream_preview
from zmovie_platform.repository import add_asset, save_project
from zmovie_platform.storyboard import create_storyboard


class MediaPreviewTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_db = storage.DB_PATH
        storage.DB_PATH = self.root / "zmovie.db"
        self.project = create_storyboard(
            name="Preview Movie",
            concept="A production project with a managed final delivery asset.",
            target_duration_seconds=20,
        )
        save_project(self.project)

    def tearDown(self):
        storage.DB_PATH = self.old_db
        self.tmp.cleanup()

    def test_media_preview_token_is_not_api_auth_token(self):
        token = auth.issue_media_preview_token(
            project_id=self.project.id,
            asset_id="asset_preview",
            subject="admin",
        )
        self.assertIsNone(auth.decode_token(token))
        payload = auth.decode_media_preview_token(token)
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["project_id"], self.project.id)
        self.assertEqual(payload["asset_id"], "asset_preview")

        api_token = auth.issue_token({"username": "admin", "role": "admin"})
        self.assertIsNone(auth.decode_media_preview_token(api_token))

    def test_managed_mp4_resolves_and_streams_inline(self):
        media_root = self.root / "media"
        project_dir = media_root / self.project.id
        project_dir.mkdir(parents=True)
        video = project_dir / "final.mp4"
        video.write_bytes(b"not-a-real-mp4-but-a-managed-preview-fixture")
        asset = add_asset(self.project.id, "final", "Final movie", str(video))

        with mock.patch.dict(os.environ, {"ZMOVIE_MEDIA_ROOT": str(media_root)}):
            loaded, path = _asset_for_preview(self.project.id, asset["id"])
            self.assertEqual(loaded["id"], asset["id"])
            self.assertEqual(path, video.resolve())

            token = auth.issue_media_preview_token(
                project_id=self.project.id,
                asset_id=asset["id"],
                subject="admin",
            )
            response = stream_preview(token)
            self.assertEqual(response.media_type, "video/mp4")
            self.assertEqual(response.headers["content-disposition"], "inline")
            self.assertEqual(response.headers["cache-control"], "private, no-store")

    def test_preview_rejects_asset_outside_managed_media_root(self):
        media_root = self.root / "media"
        media_root.mkdir()
        outside = self.root / "outside.mp4"
        outside.write_bytes(b"fixture")
        asset = add_asset(self.project.id, "final", "Outside", str(outside))

        with mock.patch.dict(os.environ, {"ZMOVIE_MEDIA_ROOT": str(media_root)}):
            with self.assertRaises(HTTPException) as ctx:
                _asset_for_preview(self.project.id, asset["id"])
        self.assertEqual(ctx.exception.status_code, 403)

    def test_preview_rejects_non_mp4_asset(self):
        media_root = self.root / "media"
        project_dir = media_root / self.project.id
        project_dir.mkdir(parents=True)
        video = project_dir / "clip.webm"
        video.write_bytes(b"fixture")
        asset = add_asset(self.project.id, "render", "WebM render", str(video))

        with mock.patch.dict(os.environ, {"ZMOVIE_MEDIA_ROOT": str(media_root)}):
            with self.assertRaises(HTTPException) as ctx:
                _asset_for_preview(self.project.id, asset["id"])
        self.assertEqual(ctx.exception.status_code, 415)


if __name__ == "__main__":
    unittest.main()
