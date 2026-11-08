"""Unit tests for the durable worker queue (worker_queue.py).

Covers enqueue/claim/heartbeat/complete/fail/recovery/pause/sanitization.
No external providers or rendering are involved.
"""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from zmovie_platform import storage
from zmovie_platform.worker_queue import (
    ACTIVE_STATES,
    TERMINAL_STATES,
    _sanitize_payload,
    claim,
    complete,
    enqueue,
    fail,
    get,
    heartbeat,
    is_paused,
    list_jobs,
    mark_running,
    queue_status,
    recover_stale,
    set_paused,
    worker_identity,
)


class WorkerQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_db = storage.DB_PATH
        storage.DB_PATH = self.root / "zmovie.db"
        storage.ensure_database()

    def tearDown(self):
        storage.DB_PATH = self.old_db
        self.tmp.cleanup()

    def test_worker_identity_is_nonempty(self):
        ident = worker_identity()
        self.assertIsInstance(ident, str)
        self.assertGreater(len(ident), 0)

    def test_enqueue_get_list_roundtrip(self):
        job = enqueue(
            "production_render",
            project_id="prj_1",
            production_run_id="run_1",
            provider="comfyui",
            payload={"shots": 3},
            priority=50,
            max_attempts=3,
        )
        self.assertTrue(job["id"].startswith("wrk_"))
        self.assertEqual(job["status"], "queued")
        self.assertEqual(job["priority"], 50)

        fetched = get(job["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["payload"], {"shots": 3})
        self.assertEqual(fetched["result"], {})

        listed = list_jobs(limit=100)
        self.assertGreaterEqual(len(listed), 1)
        ids = {item["id"] for item in listed}
        self.assertIn(job["id"], ids)

    def test_claim_and_heartbeat(self):
        enqueue("render_shot", project_id="prj_1", provider="mock")
        worker = worker_identity()
        claimed = claim(worker, lease_seconds=60)
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed["status"], "claimed")
        self.assertEqual(claimed["worker_id"], worker)

        # อ้างสิทธิ์งานเดียวกันซ้ำไม่ควรสำเร็จ (สถานะเปลี่ยนเป็น claimed แล้ว)
        claimed_again = claim(worker, lease_seconds=60)
        self.assertIsNone(claimed_again)

        ok = heartbeat(claimed["id"], worker, lease_seconds=60)
        self.assertTrue(ok)

    def test_heartbeat_wrong_worker_rejected(self):
        enqueue("render_shot", project_id="prj_1", provider="mock")
        worker_a = worker_identity()
        worker_b = worker_identity()
        claimed = claim(worker_a)
        self.assertFalse(heartbeat(claimed["id"], worker_b))

    def test_mark_running_and_complete(self):
        enqueue("render_shot", project_id="prj_1", provider="mock")
        worker = worker_identity()
        claimed = claim(worker)
        mark_running(claimed["id"], worker)
        self.assertEqual(get(claimed["id"])["status"], "running")

        complete(claimed["id"], worker, result={"output_path": "/tmp/out.mp4"})
        self.assertEqual(get(claimed["id"])["status"], "completed")
        self.assertEqual(get(claimed["id"])["result"], {"output_path": "/tmp/out.mp4"})

    def test_fail_exhausts_attempts_immediately(self):
        enqueue("render_shot", project_id="prj_1", provider="mock", max_attempts=1)
        worker = worker_identity()
        claimed = claim(worker)
        result = fail(claimed["id"], worker, RuntimeError("boom"))
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error_code"], "RuntimeError")

    def test_fail_retries_when_attempts_remain(self):
        enqueue("render_shot", project_id="prj_1", provider="mock", max_attempts=3)
        worker = worker_identity()
        claimed = claim(worker)
        result = fail(claimed["id"], worker, RuntimeError("boom"))
        self.assertEqual(result["status"], "retry_wait")
        self.assertEqual(result["attempts"], 1)

    def test_recover_stale_bilibili_lease_becomes_recovery_required(self):
        enqueue("bilibili_publish", project_id="prj_1", provider="webhook")
        worker = worker_identity()
        claimed = claim(worker, lease_seconds=1)
        time.sleep(1.2)
        recover_stale(apply=True)
        recovered = get(claimed["id"])
        self.assertEqual(recovered["status"], "recovery_required")
        self.assertEqual(recovered["error_code"], "external_state_unknown")

    def test_recover_stale_render_lease_becomes_retry_wait(self):
        enqueue("render_shot", project_id="prj_1", provider="mock", max_attempts=3)
        worker = worker_identity()
        claimed = claim(worker, lease_seconds=1)
        time.sleep(1.2)
        recover_stale(apply=True)
        recovered = get(claimed["id"])
        self.assertEqual(recovered["status"], "retry_wait")
        self.assertEqual(recovered["error_code"], "stale_lease_recovered")

    def test_pause_and_resume(self):
        set_paused(True)
        self.assertTrue(is_paused())
        set_paused(False)
        self.assertFalse(is_paused())

    def test_queue_status_shape(self):
        enqueue("render_shot", project_id="prj_1", provider="mock")
        status = queue_status()
        self.assertIn("counts", status)
        self.assertIn("active", status)
        self.assertIn("paused", status)
        self.assertIsInstance(status["paused"], bool)

    def test_sanitize_payload_rejects_secret_keys(self):
        with self.assertRaises(ValueError):
            _sanitize_payload({"password": "secret123"})
        with self.assertRaises(ValueError):
            _sanitize_payload({"data": {"token": "abc"}})
        with self.assertRaises(ValueError):
            _sanitize_payload({"Authorization": "Bearer x"})
        with self.assertRaises(TypeError):
            _sanitize_payload({"data": object()})
        clean = _sanitize_payload({"shots": 3, "nested": {"a": 1}, "list": [1, 2]})
        self.assertEqual(clean, {"shots": 3, "nested": {"a": 1}, "list": [1, 2]})

    def test_active_and_terminal_states(self):
        self.assertIn("queued", ACTIVE_STATES)
        self.assertIn("claimed", ACTIVE_STATES)
        self.assertIn("running", ACTIVE_STATES)
        self.assertIn("completed", TERMINAL_STATES)
        self.assertIn("failed", TERMINAL_STATES)


if __name__ == "__main__":
    unittest.main()
