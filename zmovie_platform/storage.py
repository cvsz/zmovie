from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("ZMOVIE_DB_PATH", "data/zmovie.db"))

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'admin',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  owner TEXT NOT NULL,
  name TEXT NOT NULL,
  concept TEXT NOT NULL,
  genre TEXT NOT NULL,
  visual_style TEXT NOT NULL,
  aspect_ratio TEXT NOT NULL,
  target_duration_seconds INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS characters (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scenes (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  order_index INTEGER NOT NULL,
  payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shots (
  id TEXT PRIMARY KEY,
  scene_id TEXT NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  order_index INTEGER NOT NULL,
  payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS render_jobs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  shot_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  status TEXT NOT NULL,
  output_path TEXT NOT NULL DEFAULT '',
  error TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  metadata TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS assets (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  name TEXT NOT NULL,
  path TEXT NOT NULL,
  metadata TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS publish_jobs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  tags TEXT NOT NULL DEFAULT '[]',
  video_path TEXT NOT NULL,
  cover_path TEXT NOT NULL DEFAULT '',
  subtitle_path TEXT NOT NULL DEFAULT '',
  playlist TEXT NOT NULL DEFAULT '',
  content_type TEXT NOT NULL DEFAULT 'Original',
  schedule_at TEXT NOT NULL DEFAULT '',
  published_url TEXT NOT NULL DEFAULT '',
  error TEXT NOT NULL DEFAULT '',
  metadata TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS worker_jobs (
  id TEXT PRIMARY KEY,
  job_type TEXT NOT NULL,
  project_id TEXT NOT NULL DEFAULT '',
  production_run_id TEXT NOT NULL DEFAULT '',
  provider TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 100,
  attempts INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 3,
  worker_id TEXT NOT NULL DEFAULT '',
  claimed_at TEXT NOT NULL DEFAULT '',
  heartbeat_at TEXT NOT NULL DEFAULT '',
  lease_expires_at TEXT NOT NULL DEFAULT '',
  started_at TEXT NOT NULL DEFAULT '',
  next_attempt_at TEXT NOT NULL DEFAULT '',
  completed_at TEXT NOT NULL DEFAULT '',
  failed_at TEXT NOT NULL DEFAULT '',
  result_json TEXT NOT NULL DEFAULT '{}',
  error_code TEXT NOT NULL DEFAULT '',
  error_message TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runtime_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scenes_project ON scenes(project_id, order_index);
CREATE INDEX IF NOT EXISTS idx_shots_project ON shots(project_id, scene_id, order_index);
CREATE INDEX IF NOT EXISTS idx_jobs_project ON render_jobs(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_assets_project ON assets(project_id, kind);
CREATE INDEX IF NOT EXISTS idx_publish_project ON publish_jobs(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_publish_status ON publish_jobs(status, created_at);
CREATE INDEX IF NOT EXISTS idx_worker_jobs_claim ON worker_jobs(status, priority, next_attempt_at, created_at);
CREATE INDEX IF NOT EXISTS idx_worker_jobs_project ON worker_jobs(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_worker_jobs_lease ON worker_jobs(status, lease_expires_at);
"""


def ensure_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    ensure_database()
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def loads(value: str | None, default: Any = None) -> Any:
    if not value:
        return default
    return json.loads(value)
