from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from zmovie_platform import storage
from zmovie_platform.worker_queue import (
    claim,
    complete,
    enqueue,
    fail,
    get,
    heartbeat,
    is_paused,
    mark_running,
    queue_status,
    recover_stale,
    set_paused,
)


class WorkerQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.original_db = storage.DB_PATH
        storage.DB_PATH = Path(self.tmp.name) / "queue.db"
        storage.ensure_database()

    def tearDown(self) -> None:
        storage.DB_PATH = self.original_db
        self.tmp.cleanup()

    def test_enqueue_claim_heartbeat_complete(self) -> None:
        item = enqueue("production_render", project_id="prj_test", provider="comfyui", payload={"max_workers": 2})
        self.assertEqual(item["status"], "queued")
        claimed = claim("worker-a", lease_seconds=60)
        self.assertIsNotNone(claimed)
        assert claimed is not None
        self.assertEqual(claimed["id"], item["id"])
        self.assertIsNone(claim("worker-b", lease_seconds=60))
        mark_running(item["id"], "worker-a", lease_seconds=60)
        self.assertTrue(heartbeat(item["id"], "worker-a", lease_seconds=60))
        complete(item["id"], "worker-a", {"ok": True})
        final = get(item["id"])
        assert final is not None
        self.assertEqual(final["status"], "completed")
        self.assertEqual(final["result"], {"ok": True})

    def test_sensitive_payload_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            enqueue("production_run", payload={"api_token": "secret"})
        with self.assertRaises(ValueError):
            enqueue("production_run", payload={"nested": {"browser_state": "x"}})

    def test_failure_retries_then_exhausts(self) -> None:
        item = enqueue("production_render", project_id="prj_test", max_attempts=2)
        claimed = claim("worker-a")
        assert claimed is not None
        mark_running(item["id"], "worker-a")
        first = fail(item["id"], "worker-a", RuntimeError("boom"), retry_delay_seconds=1)
        self.assertEqual(first["status"], "retry_wait")
        with storage.connect() as conn:
            conn.execute("UPDATE worker_jobs SET next_attempt_at='' WHERE id=?", (item["id"],))
        claimed2 = claim("worker-b")
        assert claimed2 is not None
        mark_running(item["id"], "worker-b")
        second = fail(item["id"], "worker-b", RuntimeError("boom again"), retry_delay_seconds=1)
        self.assertEqual(second["status"], "failed")
        self.assertEqual(second["attempts"], 2)

    def test_stale_lease_recovery(self) -> None:
        item = enqueue("production_render", project_id="prj_test", max_attempts=3)
        claimed = claim("worker-a")
        assert claimed is not None
        mark_running(item["id"], "worker-a")
        stale = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        with storage.connect() as conn:
            conn.execute("UPDATE worker_jobs SET lease_expires_at=? WHERE id=?", (stale, item["id"]))
        preview = recover_stale(apply=False)
        self.assertEqual([row["id"] for row in preview], [item["id"]])
        recover_stale(apply=True)
        recovered = get(item["id"])
        assert recovered is not None
        self.assertEqual(recovered["status"], "retry_wait")
        self.assertEqual(recovered["error_code"], "stale_lease_recovered")

    def test_bilibili_stale_state_never_blindly_retries(self) -> None:
        item = enqueue("bilibili_publish", project_id="prj_test")
        claimed = claim("worker-a")
        assert claimed is not None
        mark_running(item["id"], "worker-a")
        stale = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        with storage.connect() as conn:
            conn.execute("UPDATE worker_jobs SET lease_expires_at=? WHERE id=?", (stale, item["id"]))
        recover_stale(apply=True)
        recovered = get(item["id"])
        assert recovered is not None
        self.assertEqual(recovered["status"], "recovery_required")
        self.assertEqual(recovered["error_code"], "external_state_unknown")

    def test_pause_resume_and_status(self) -> None:
        self.assertFalse(is_paused())
        set_paused(True)
        self.assertTrue(is_paused())
        enqueue("production_render", project_id="prj_test")
        status = queue_status()
        self.assertTrue(status["paused"])
        self.assertEqual(status["counts"]["queued"], 1)
        set_paused(False)
        self.assertFalse(is_paused())


if __name__ == "__main__":
    unittest.main()
