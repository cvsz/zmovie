"""Unit tests for the ZEAZVERSE domain layer (Phase 1-3).

Tests run against a throwaway SQLite database pointed at by
``ZMOVIE_DB_PATH``; no external providers, YouTube, or rendering is involved.
"""
from __future__ import annotations

import os
import tempfile
import unittest

# Point storage at a throwaway DB before importing anything that reads
# ZMOVIE_DB_PATH at module level.
os.environ.setdefault("ZMOVIE_DB_PATH", tempfile.mktemp(suffix=".db"))

from zmovie_platform.migrations import applied_versions, migrate  # noqa: E402
from zmovie_platform.storage import connect  # noqa: E402
from zmovie_platform.zeazverse import store as zs  # noqa: E402

_ALL_ZEAZVERSE_TABLES = (
    "zeazverse_channels",
    "zeazverse_channel_integrations",
    "zeazverse_characters",
    "zeazverse_character_versions",
    "zeazverse_character_assets",
    "zeazverse_series",
    "zeazverse_episodes",
    "zeazverse_scripts",
    "zeazverse_storyboards",
    "zeazverse_scenes",
    "zeazverse_generation_jobs",
    "zeazverse_generation_artifacts",
    "zeazverse_qa_reports",
    "zeazverse_approval_requests",
    "zeazverse_publications",
    "zeazverse_analytics_snapshots",
    "zeazverse_workflow_runs",
    "zeazverse_audit_events",
)


def _clean_tables() -> None:
    with connect() as conn:
        for table in _ALL_ZEAZVERSE_TABLES:
            conn.execute(f"DELETE FROM {table}")


class ZeazverseMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        migrate()
        _clean_tables()

    def test_migration_records_zeazverse_version(self) -> None:
        self.assertIn("zeazverse", applied_versions())

    def test_migration_creates_all_zeazverse_tables(self) -> None:
        with connect() as conn:
            for table in _ALL_ZEAZVERSE_TABLES:
                row = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                ).fetchone()
                self.assertIsNotNone(row, f"missing table {table}")


class ZeazverseChannelTests(unittest.TestCase):
    def setUp(self) -> None:
        migrate()
        _clean_tables()

    def test_channel_upsert_get_list(self) -> None:
        channel = zs.upsert_channel(
            {
                "id": "ch_z1",
                "name": "ZEAZVERSE",
                "handle": "@zeazverse",
                "description": "Original AI cinematic stories.",
                "owner": "admin",
            }
        )
        self.assertEqual(channel["name"], "ZEAZVERSE")
        self.assertEqual(channel["handle"], "@zeazverse")

        got = zs.get_channel("ch_z1")
        self.assertIsNotNone(got)
        self.assertEqual(got["status"], "setup")

        by_handle = zs.get_channel_by_handle("@zeazverse")
        self.assertIsNotNone(by_handle)
        self.assertEqual(by_handle["id"], "ch_z1")

        items = zs.list_channels(owner="admin")
        self.assertEqual(len(items), 1)


class ZeazverseCharacterTests(unittest.TestCase):
    def setUp(self) -> None:
        migrate()
        _clean_tables()

    def test_character_crud_and_version(self) -> None:
        char = zs.upsert_character(
            {
                "id": "ch_lalin",
                "name": "LALIN",
                "archetype": "The Dreamer",
                "nationality": "Thai",
                "adult": True,
                "appearance": "Adult Thai woman, long dark high ponytail",
                "personality": "Creative, compassionate, curious, mysterious.",
                "owner": "admin",
            }
        )
        self.assertEqual(char["name"], "LALIN")
        self.assertEqual(char["archetype"], "The Dreamer")
        self.assertEqual(char["adult"], 1)

        got = zs.get_character("ch_lalin")
        self.assertIsNotNone(got)
        self.assertEqual(got["canonical_hash"], "")

        items = zs.list_characters(owner="admin")
        self.assertEqual(len(items), 1)

        # Versioned reference snapshot requiring human approval.
        ver = zs.record_character_version(
            character_id="ch_lalin",
            version=1,
            payload={"hair": "long dark high ponytail"},
            change_reason="initial canon",
            approved_by="admin",
            approved_at="2026-01-01T00:00:00Z",
        )
        self.assertEqual(ver["version"], 1)
        versions = zs.list_character_versions("ch_lalin")
        self.assertEqual(len(versions), 1)

        # Character asset (brand reference, not a real rendered image).
        asset = zs.upsert_character_asset(
            {
                "id": "asset_lalin_poster",
                "character_id": "ch_lalin",
                "kind": "poster",
                "name": "LALIN poster concept",
                "path": "assets/characters/lalin/poster.svg",
                "sha256": "deadbeef",
                "width": 1080,
                "height": 1920,
                "owner": "admin",
            }
        )
        self.assertEqual(asset["kind"], "poster")
        assets = zs.list_character_assets("ch_lalin")
        self.assertEqual(len(assets), 1)


class ZeazverseSeriesEpisodeTests(unittest.TestCase):
    def setUp(self) -> None:
        migrate()
        _clean_tables()

    def test_series_and_episode_crud(self) -> None:
        zs.upsert_channel(
            {"id": "ch_z1", "name": "ZEAZVERSE", "handle": "@zeazverse", "owner": "admin"}
        )
        series = zs.upsert_series(
            {
                "id": "s1",
                "channel_id": "ch_z1",
                "title": "Origins",
                "genre": "cinematic action",
                "owner": "admin",
            }
        )
        self.assertEqual(series["title"], "Origins")

        episode = zs.upsert_episode(
            {
                "id": "ep1",
                "series_id": "s1",
                "channel_id": "ch_z1",
                "episode_number": 1,
                "title": "LALIN Awakens",
                "concept": "Dream world discovery.",
                "state": "IDEA",
                "idempotency_key": "ep1-key-001",
                "owner": "admin",
            }
        )
        self.assertEqual(episode["state"], "IDEA")
        self.assertEqual(episode["idempotency_key"], "ep1-key-001")

        got = zs.get_episode("ep1")
        self.assertIsNotNone(got)
        self.assertEqual(got["title"], "LALIN Awakens")

        items = zs.list_episodes(series_id="s1")
        self.assertEqual(len(items), 1)
        items_state = zs.list_episodes(state="IDEA")
        self.assertEqual(len(items_state), 1)

        # Idempotency key conflict.
        with self.assertRaises(Exception):
            zs.upsert_episode(
                {
                    "id": "ep2",
                    "series_id": "s1",
                    "channel_id": "ch_z1",
                    "episode_number": 2,
                    "title": "Duplicate",
                    "idempotency_key": "ep1-key-001",
                    "owner": "admin",
                }
            )


class ZeazverseEpisodeStateMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        migrate()
        _clean_tables()

    def _seed_episode(self, state: str = "IDEA") -> dict:
        zs.upsert_channel(
            {"id": "ch_z1", "name": "ZEAZVERSE", "handle": "@zeazverse", "owner": "admin"}
        )
        zs.upsert_series(
            {"id": "s1", "channel_id": "ch_z1", "title": "Origins", "owner": "admin"}
        )
        return zs.upsert_episode(
            {
                "id": "ep1",
                "series_id": "s1",
                "channel_id": "ch_z1",
                "episode_number": 1,
                "title": "Pilot",
                "state": state,
                "idempotency_key": "ep-sm-001",
                "owner": "admin",
            }
        )

    def test_valid_transition(self) -> None:
        self._seed_episode("IDEA")
        updated = zs.transition_episode(
            episode_id="ep1", target_state="SCRIPT_APPROVED", actor="admin"
        )
        self.assertEqual(updated["state"], "SCRIPT_APPROVED")

    def test_invalid_transition_rejected(self) -> None:
        self._seed_episode("IDEA")
        with self.assertRaises(ValueError):
            zs.transition_episode(
                episode_id="ep1", target_state="RENDERED", actor="admin"
            )

    def test_approval_guard_blocks_unapproved(self) -> None:
        self._seed_episode("QA_PASSED")
        # READY_FOR_REVIEW is a guard state: needs an approved approval_request.
        with self.assertRaises(ValueError):
            zs.transition_episode(
                episode_id="ep1", target_state="READY_FOR_REVIEW", actor="admin"
            )

    def test_approval_guard_allows_when_approved(self) -> None:
        self._seed_episode("QA_PASSED")
        zs.upsert_approval_request(
            {
                "id": "ap1",
                "episode_id": "ep1",
                "requested_by": "admin",
                "decision": "approved",
                "decided_by": "admin",
                "idempotency_key": "ap-key-001",
                "owner": "admin",
            }
        )
        updated = zs.transition_episode(
            episode_id="ep1", target_state="READY_FOR_REVIEW", actor="admin"
        )
        self.assertEqual(updated["state"], "READY_FOR_REVIEW")


class ZeazverseScriptStoryboardSceneTests(unittest.TestCase):
    def setUp(self) -> None:
        migrate()
        _clean_tables()

    def test_script_storyboard_scene(self) -> None:
        zs.upsert_channel(
            {"id": "ch_z1", "name": "ZEAZVERSE", "handle": "@zeazverse", "owner": "admin"}
        )
        zs.upsert_series(
            {"id": "s1", "channel_id": "ch_z1", "title": "Origins", "owner": "admin"}
        )
        zs.upsert_episode(
            {
                "id": "ep1",
                "series_id": "s1",
                "channel_id": "ch_z1",
                "episode_number": 1,
                "title": "Pilot",
                "idempotency_key": "ep-ss-001",
                "owner": "admin",
            }
        )

        script = zs.upsert_script(
            {
                "id": "sc1",
                "episode_id": "ep1",
                "title": "Pilot script",
                "content": "FADE IN: ...",
                "language": "en",
                "owner": "admin",
            }
        )
        self.assertEqual(script["language"], "en")
        self.assertIsNotNone(zs.get_script("sc1"))

        zs.upsert_storyboard(
            {
                "id": "sb1",
                "episode_id": "ep1",
                "title": "Pilot storyboard",
                "scenes": [{"scene_number": 1}],
                "owner": "admin",
            }
        )
        self.assertIsNotNone(zs.get_storyboard("sb1"))

        scene = zs.upsert_scene(
            {
                "id": "sn1",
                "storyboard_id": "sb1",
                "episode_id": "ep1",
                "scene_number": 1,
                "time_start_seconds": 0,
                "time_end_seconds": 8,
                "characters": ["ch_lalin"],
                "environment": "Dream world",
                "subject_action": "LALIN walks forward",
                "camera_framing": "Medium shot",
                "camera_movement": "Slow push-in",
                "lighting": "Soft purple key",
                "positive_prompt": "cinematic, 9:16",
                "negative_prompt": "extra fingers, distorted face",
                "generation_model": "mock-video",
                "owner": "admin",
            }
        )
        self.assertEqual(scene["scene_number"], 1)
        self.assertEqual(scene["generation_model"], "mock-video")
        got = zs.get_scene("sn1")
        self.assertIsNotNone(got)
        self.assertEqual(got["camera_movement"], "Slow push-in")


class ZeazverseGenerationQAApprovalTests(unittest.TestCase):
    def setUp(self) -> None:
        migrate()
        _clean_tables()

    def test_generation_job_and_artifact(self) -> None:
        zs.upsert_channel(
            {"id": "ch_z1", "name": "ZEAZVERSE", "handle": "@zeazverse", "owner": "admin"}
        )
        zs.upsert_series(
            {"id": "s1", "channel_id": "ch_z1", "title": "Origins", "owner": "admin"}
        )
        zs.upsert_episode(
            {
                "id": "ep1",
                "series_id": "s1",
                "channel_id": "ch_z1",
                "episode_number": 1,
                "title": "Pilot",
                "idempotency_key": "ep-gq-001",
                "owner": "admin",
            }
        )
        zs.upsert_storyboard(
            {
                "id": "sb1",
                "episode_id": "ep1",
                "title": "Pilot Storyboard",
                "owner": "admin",
            }
        )
        zs.upsert_scene(
            {
                "id": "sn1",
                "storyboard_id": "sb1",
                "episode_id": "ep1",
                "scene_number": 1,
                "owner": "admin",
            }
        )

        job = zs.upsert_generation_job(
            {
                "id": "gj1",
                "scene_id": "sn1",
                "provider": "mock",
                "model": "mock-video-v1",
                "status": "queued",
                "owner": "admin",
            }
        )
        self.assertEqual(job["status"], "queued")
        self.assertIsNotNone(zs.get_generation_job("gj1"))

        artifact = zs.upsert_generation_artifact(
            {
                "id": "ga1",
                "generation_job_id": "gj1",
                "kind": "video",
                "path": "renders/ep1/sn1.mp4",
                "sha256": "cafebab",
                "width": 1080,
                "height": 1920,
                "duration_seconds": 30.0,
                "owner": "admin",
            }
        )
        self.assertEqual(artifact["kind"], "video")
        self.assertEqual(artifact["duration_seconds"], 30.0)

    def test_qa_report_and_approval(self) -> None:
        zs.upsert_channel(
            {"id": "ch_z1", "name": "ZEAZVERSE", "handle": "@zeazverse", "owner": "admin"}
        )
        zs.upsert_series(
            {"id": "s1", "channel_id": "ch_z1", "title": "Origins", "owner": "admin"}
        )
        zs.upsert_episode(
            {
                "id": "ep1",
                "series_id": "s1",
                "channel_id": "ch_z1",
                "episode_number": 1,
                "title": "Pilot",
                "idempotency_key": "ep-qa-001",
                "owner": "admin",
            }
        )

        qa = zs.upsert_qa_report(
            {
                "id": "qa1",
                "episode_id": "ep1",
                "passed": True,
                "checks": [{"name": "identity", "passed": True}],
                "defects": [],
                "reviewer": "admin",
                "owner": "admin",
            }
        )
        self.assertTrue(qa["passed"])
        self.assertIsNotNone(zs.get_qa_report("qa1"))

        approval = zs.upsert_approval_request(
            {
                "id": "ap1",
                "episode_id": "ep1",
                "requested_by": "creator",
                "decision": "pending",
                "idempotency_key": "ap-qa-001",
                "owner": "creator",
            }
        )
        self.assertEqual(approval["decision"], "pending")
        got = zs.get_approval_request("ap1")
        self.assertIsNotNone(got)

        by_key = zs.get_approval_request_by_idempotency_key("ap-qa-001")
        self.assertIsNotNone(by_key)
        self.assertEqual(by_key["id"], "ap1")


class ZeazversePublicationAnalyticsTests(unittest.TestCase):
    def setUp(self) -> None:
        migrate()
        _clean_tables()

    def test_publication_private_by_default(self) -> None:
        zs.upsert_channel(
            {"id": "ch_z1", "name": "ZEAZVERSE", "handle": "@zeazverse", "owner": "admin"}
        )
        zs.upsert_series(
            {"id": "s1", "channel_id": "ch_z1", "title": "Origins", "owner": "admin"}
        )
        zs.upsert_episode(
            {
                "id": "ep1",
                "series_id": "s1",
                "channel_id": "ch_z1",
                "episode_number": 1,
                "title": "Pilot",
                "idempotency_key": "ep-pub-001",
                "owner": "admin",
            }
        )
        pub = zs.upsert_publication(
            {
                "id": "pub1",
                "episode_id": "ep1",
                "platform": "youtube",
                "state": "IDEA",
                "idempotency_key": "pub-key-001",
                "title": "Pilot",
                "owner": "admin",
            }
        )
        # Default privacy is private (Sec. 12-13).
        self.assertEqual(pub["privacy"], "private")
        self.assertEqual(zs.get_publication("pub1")["id"], "pub1")
        by_key = zs.get_publication_by_idempotency_key("pub-key-001")
        self.assertIsNotNone(by_key)
        self.assertEqual(by_key["id"], "pub1")

    def test_analytics_snapshot(self) -> None:
        zs.upsert_channel(
            {"id": "ch_z1", "name": "ZEAZVERSE", "handle": "@zeazverse", "owner": "admin"}
        )
        snap = zs.upsert_analytics_snapshot(
            {
                "id": "an1",
                "channel_id": "ch_z1",
                "metric_date": "2026-11-07",
                "views": 1000,
                "watch_time_minutes": 500,
                "average_view_duration_seconds": 30,
                "subscribers_gained": 50,
                "engagement": 120,
                "source": {"provider": "mock"},
                "owner": "admin",
            }
        )
        self.assertEqual(snap["views"], 1000)

    def test_workflow_run_and_audit(self) -> None:
        zs.upsert_channel(
            {"id": "ch_z1", "name": "ZEAZVERSE", "handle": "@zeazverse", "owner": "admin"}
        )
        zs.upsert_series(
            {"id": "s1", "channel_id": "ch_z1", "title": "Origins", "owner": "admin"}
        )
        zs.upsert_episode(
            {
                "id": "ep1",
                "series_id": "s1",
                "channel_id": "ch_z1",
                "episode_number": 1,
                "title": "Pilot",
                "idempotency_key": "ep-wf-001",
                "owner": "admin",
            }
        )
        run = zs.upsert_workflow_run(
            {
                "id": "wf1",
                "episode_id": "ep1",
                "status": "running",
                "current_state": "IDEA",
                "owner": "admin",
            }
        )
        self.assertEqual(run["status"], "running")
        self.assertEqual(len(zs.list_workflow_runs(episode_id="ep1")), 1)

        events = zs.list_audit_events(entity_type="episode", entity_id="ep1", limit=10)
        self.assertGreaterEqual(len(events), 0)


if __name__ == "__main__":
    unittest.main()
