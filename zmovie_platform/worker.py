from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import threading
from typing import Any

from .pipeline import render_shot
from .production import execute_production_run, render_all_production
from .worker_queue import claim, complete, fail, heartbeat, is_paused, mark_running, recover_stale, worker_identity

LOG = logging.getLogger("zmovie.worker")
_STOP = threading.Event()


def _install_signals() -> None:
    def stop(_signum: int, _frame: Any) -> None:
        _STOP.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)


def _execute(job: dict[str, Any]) -> dict[str, Any]:
    job_type = str(job.get("job_type") or "")
    project_id = str(job.get("project_id") or "")
    payload = dict(job.get("payload") or {})
    if job_type == "production_run":
        run_id = str(job.get("production_run_id") or payload.get("run_id") or "")
        if not project_id or not run_id:
            raise ValueError("production_run job requires project_id and production_run_id")
        return execute_production_run(project_id, run_id)
    if job_type == "production_render":
        provider = str(job.get("provider") or payload.get("provider") or "")
        max_workers = int(payload.get("max_workers") or 2)
        if not project_id or not provider:
            raise ValueError("production_render job requires project_id and provider")
        return render_all_production(project_id, provider, max_workers)
    raise ValueError(f"unsupported worker job type: {job_type}")


def run_once(worker_id: str, *, lease_seconds: int = 120) -> bool:
    job = claim(worker_id, lease_seconds=lease_seconds, allowed_types=("production_run", "production_render"))
    if job is None:
        return False
    job_id = str(job["id"])
    mark_running(job_id, worker_id, lease_seconds=lease_seconds)
    stop_heartbeat = threading.Event()

    def beat() -> None:
        interval = max(5, min(30, lease_seconds // 3))
        while not stop_heartbeat.wait(interval):
            try:
                heartbeat(job_id, worker_id, lease_seconds=lease_seconds)
            except Exception:
                LOG.exception("heartbeat failed job_id=%s", job_id)

    thread = threading.Thread(target=beat, name=f"heartbeat-{job_id}", daemon=True)
    thread.start()
    try:
        LOG.info("worker job start id=%s type=%s project=%s", job_id, job.get("job_type"), job.get("project_id"))
        result = _execute(job)
        complete(job_id, worker_id, result)
        LOG.info("worker job complete id=%s", job_id)
    except Exception as exc:
        state = fail(job_id, worker_id, exc, retry_delay_seconds=int(os.getenv("ZMOVIE_WORKER_RETRY_DELAY", "30")))
        LOG.error("worker job failed id=%s next_state=%s error_type=%s", job_id, state.get("status"), type(exc).__name__)
    finally:
        stop_heartbeat.set()
        thread.join(timeout=2)
    return True


def serve() -> int:
    logging.basicConfig(level=os.getenv("ZMOVIE_LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    _install_signals()
    worker_id = worker_identity()
    lease_seconds = max(30, int(os.getenv("ZMOVIE_WORKER_LEASE_SECONDS", "120")))
    poll_seconds = max(1.0, float(os.getenv("ZMOVIE_WORKER_POLL_SECONDS", "2")))
    recovered = recover_stale(apply=True)
    LOG.info("worker started id=%s recovered_stale=%s", worker_id, len(recovered))
    while not _STOP.is_set():
        if is_paused():
            _STOP.wait(poll_seconds)
            continue
        worked = run_once(worker_id, lease_seconds=lease_seconds)
        if not worked:
            _STOP.wait(poll_seconds)
    LOG.info("worker stopping id=%s", worker_id)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="zMovie render worker")
    parser.add_argument("project_id", nargs="?")
    parser.add_argument("shot_id", nargs="?")
    parser.add_argument("--provider", default="mock")
    parser.add_argument("--once", action="store_true", help="process at most one durable queued job")
    parser.add_argument("--recover", action="store_true", help="apply stale lease recovery and exit")
    args = parser.parse_args()
    if args.recover:
        print(json.dumps(recover_stale(apply=True), ensure_ascii=False, indent=2, default=str))
        return 0
    if args.project_id and args.shot_id:
        result = render_shot(args.project_id, args.shot_id, args.provider)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") != "failed" else 1
    if args.once:
        logging.basicConfig(level=logging.INFO)
        run_once(worker_identity())
        return 0
    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
