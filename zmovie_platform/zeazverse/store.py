"""ZEAZVERSE persistence: characters, series, episodes, scripts, storyboards,
generation jobs, QA reports, approval requests, publications, audit events.

All tables use the ``zeazverse_`` prefix so they never collide with the
existing zMovie v2 schema (users, projects, characters, scenes, shots,
render_jobs, assets, publish_jobs, worker_jobs, ...).

Schema is idempotent (CREATE TABLE IF NOT EXISTS) so current deployments can
upgrade without destructive migrations.
"""
from __future__ import annotations

import json
from typing import Any

from ..models import utcnow
from ..storage import connect

__all__ = ["utcnow", "ensure_tables", "connect", "TABLE_SQL"]

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS zeazverse_channels (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  handle TEXT UNIQUE NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'setup',
  country TEXT NOT NULL DEFAULT 'TH',
  language TEXT NOT NULL DEFAULT 'en',
  audience_made_for_kids INTEGER NOT NULL DEFAULT 0,
  branding_hash TEXT NOT NULL DEFAULT '',
  owner TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS zeazverse_channel_integrations (
  id TEXT PRIMARY KEY,
  channel_id TEXT NOT NULL REFERENCES zeazverse_channels(id) ON DELETE CASCADE,
  provider TEXT NOT NULL DEFAULT 'youtube',
  channel_id_external TEXT NOT NULL DEFAULT '',
  access_token_encrypted TEXT NOT NULL DEFAULT '',
  refresh_token_encrypted TEXT NOT NULL DEFAULT '',
  token_expires_at TEXT NOT NULL DEFAULT '',
  scopes TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS zeazverse_characters (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  archetype TEXT NOT NULL,
  nationality TEXT NOT NULL DEFAULT 'Thai',
  adult INTEGER NOT NULL DEFAULT 1,
  appearance TEXT NOT NULL DEFAULT '',
  hair TEXT NOT NULL DEFAULT '',
  wardrobe TEXT NOT NULL DEFAULT '',
  personality TEXT NOT NULL DEFAULT '',
  voice_profile TEXT NOT NULL DEFAULT '',
  visual_continuity_rules TEXT NOT NULL DEFAULT '[]',
  reference_assets TEXT NOT NULL DEFAULT '[]',
  canonical_hash TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'draft',
  owner TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS zeazverse_character_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  character_id TEXT NOT NULL REFERENCES zeazverse_characters(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  change_reason TEXT NOT NULL DEFAULT '',
  approved_by TEXT NOT NULL DEFAULT '',
  approved_at TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zc_versions_char ON zeazverse_character_versions(character_id, version);
CREATE TABLE IF NOT EXISTS zeazverse_character_assets (
  id TEXT PRIMARY KEY,
  character_id TEXT NOT NULL REFERENCES zeazverse_characters(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  name TEXT NOT NULL,
  path TEXT NOT NULL,
  sha256 TEXT NOT NULL DEFAULT '',
  width INTEGER NOT NULL DEFAULT 0,
  height INTEGER NOT NULL DEFAULT 0,
  duration_seconds REAL NOT NULL DEFAULT 0,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  owner TEXT NOT NULL DEFAULT 'local',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zc_assets_char ON zeazverse_character_assets(character_id, kind);
CREATE TABLE IF NOT EXISTS zeazverse_series (
  id TEXT PRIMARY KEY,
  channel_id TEXT NOT NULL REFERENCES zeazverse_channels(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  concept TEXT NOT NULL DEFAULT '',
  genre TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'planning',
  owner TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zseries_channel ON zeazverse_series(channel_id, status);
CREATE TABLE IF NOT EXISTS zeazverse_episodes (
  id TEXT PRIMARY KEY,
  series_id TEXT NOT NULL REFERENCES zeazverse_series(id) ON DELETE CASCADE,
  channel_id TEXT NOT NULL REFERENCES zeazverse_channels(id) ON DELETE CASCADE,
  episode_number INTEGER NOT NULL,
  title TEXT NOT NULL,
  concept TEXT NOT NULL DEFAULT '',
  state TEXT NOT NULL DEFAULT 'IDEA',
  idempotency_key TEXT UNIQUE NOT NULL,
  script_id TEXT NOT NULL DEFAULT '',
  storyboard_id TEXT NOT NULL DEFAULT '',
  render_job_id TEXT NOT NULL DEFAULT '',
  qa_report_id TEXT NOT NULL DEFAULT '',
  approval_request_id TEXT NOT NULL DEFAULT '',
  publication_id TEXT NOT NULL DEFAULT '',
  owner TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zeps_series ON zeazverse_episodes(series_id, episode_number);
CREATE INDEX IF NOT EXISTS idx_zeps_state ON zeazverse_episodes(state, created_at);
CREATE INDEX IF NOT EXISTS idx_zeps_channel ON zeazverse_episodes(channel_id, state);
CREATE TABLE IF NOT EXISTS zeazverse_scripts (
  id TEXT PRIMARY KEY,
  episode_id TEXT NOT NULL REFERENCES zeazverse_episodes(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  content TEXT NOT NULL DEFAULT '',
  language TEXT NOT NULL DEFAULT 'en',
  thai_localization TEXT NOT NULL DEFAULT '{}',
  version INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'draft',
  owner TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zscripts_episode ON zeazverse_scripts(episode_id, version);
CREATE TABLE IF NOT EXISTS zeazverse_storyboards (
  id TEXT PRIMARY KEY,
  episode_id TEXT NOT NULL REFERENCES zeazverse_episodes(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  scenes_json TEXT NOT NULL DEFAULT '[]',
  version INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'draft',
  owner TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zstoryboards_episode ON zeazverse_storyboards(episode_id, version);
CREATE TABLE IF NOT EXISTS zeazverse_scenes (
  id TEXT PRIMARY KEY,
  storyboard_id TEXT NOT NULL REFERENCES zeazverse_storyboards(id) ON DELETE CASCADE,
  episode_id TEXT NOT NULL REFERENCES zeazverse_episodes(id) ON DELETE CASCADE,
  scene_number INTEGER NOT NULL,
  time_start_seconds INTEGER NOT NULL DEFAULT 0,
  time_end_seconds INTEGER NOT NULL DEFAULT 30,
  characters_json TEXT NOT NULL DEFAULT '[]',
  environment TEXT NOT NULL DEFAULT '',
  subject_action TEXT NOT NULL DEFAULT '',
  camera_framing TEXT NOT NULL DEFAULT '',
  camera_movement TEXT NOT NULL DEFAULT '',
  lighting TEXT NOT NULL DEFAULT '',
  dialogue TEXT NOT NULL DEFAULT '',
  audio TEXT NOT NULL DEFAULT '',
  positive_prompt TEXT NOT NULL DEFAULT '',
  negative_prompt TEXT NOT NULL DEFAULT '',
  first_frame_continuity TEXT NOT NULL DEFAULT '',
  last_frame_continuity TEXT NOT NULL DEFAULT '',
  generation_model TEXT NOT NULL DEFAULT '',
  model_settings_json TEXT NOT NULL DEFAULT '{}',
  expected_output TEXT NOT NULL DEFAULT '',
  qa_checks_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'draft',
  owner TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zscenes_storyboard ON zeazverse_scenes(storyboard_id, scene_number);
CREATE INDEX IF NOT EXISTS idx_zscenes_episode ON zeazverse_scenes(episode_id, scene_number);
CREATE TABLE IF NOT EXISTS zeazverse_generation_jobs (
  id TEXT PRIMARY KEY,
  scene_id TEXT NOT NULL REFERENCES zeazverse_scenes(id) ON DELETE CASCADE,
  provider TEXT NOT NULL DEFAULT '',
  model TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'queued',
  input_hash TEXT NOT NULL DEFAULT '',
  output_path TEXT NOT NULL DEFAULT '',
  error TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zgenjobs_scene ON zeazverse_generation_jobs(scene_id, status);
CREATE TABLE IF NOT EXISTS zeazverse_generation_artifacts (
  id TEXT PRIMARY KEY,
  generation_job_id TEXT NOT NULL REFERENCES zeazverse_generation_jobs(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  path TEXT NOT NULL,
  sha256 TEXT NOT NULL DEFAULT '',
  width INTEGER NOT NULL DEFAULT 0,
  height INTEGER NOT NULL DEFAULT 0,
  duration_seconds REAL NOT NULL DEFAULT 0,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zartifacts_job ON zeazverse_generation_artifacts(generation_job_id, kind);
CREATE TABLE IF NOT EXISTS zeazverse_qa_reports (
  id TEXT PRIMARY KEY,
  episode_id TEXT NOT NULL REFERENCES zeazverse_episodes(id) ON DELETE CASCADE,
  passed INTEGER NOT NULL DEFAULT 0,
  checks_json TEXT NOT NULL DEFAULT '[]',
  defects_json TEXT NOT NULL DEFAULT '[]',
  reviewer TEXT NOT NULL DEFAULT '',
  reviewed_at TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zqa_episode ON zeazverse_qa_reports(episode_id, created_at);
CREATE TABLE IF NOT EXISTS zeazverse_approval_requests (
  id TEXT PRIMARY KEY,
  episode_id TEXT NOT NULL REFERENCES zeazverse_episodes(id) ON DELETE CASCADE,
  requested_by TEXT NOT NULL DEFAULT '',
  requested_at TEXT NOT NULL DEFAULT '',
  decided_by TEXT NOT NULL DEFAULT '',
  decided_at TEXT NOT NULL DEFAULT '',
  decision TEXT NOT NULL DEFAULT 'pending',
  justification TEXT NOT NULL DEFAULT '',
  idempotency_key TEXT UNIQUE NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zapprovals_episode ON zeazverse_approval_requests(episode_id, decision);
CREATE TABLE IF NOT EXISTS zeazverse_publications (
  id TEXT PRIMARY KEY,
  episode_id TEXT NOT NULL REFERENCES zeazverse_episodes(id) ON DELETE CASCADE,
  platform TEXT NOT NULL DEFAULT 'youtube',
  state TEXT NOT NULL DEFAULT 'IDEA',
  idempotency_key TEXT UNIQUE NOT NULL,
  owner TEXT NOT NULL DEFAULT 'local',
  external_id TEXT NOT NULL DEFAULT '',
  external_url TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  tags_json TEXT NOT NULL DEFAULT '[]',
  playlist TEXT NOT NULL DEFAULT '',
  privacy TEXT NOT NULL DEFAULT 'private',
  schedule_at TEXT NOT NULL DEFAULT '',
  published_at TEXT NOT NULL DEFAULT '',
  error TEXT NOT NULL DEFAULT '',
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zpublications_episode ON zeazverse_publications(episode_id, state);
CREATE INDEX IF NOT EXISTS idx_zpublications_state ON zeazverse_publications(state, created_at);
CREATE TABLE IF NOT EXISTS zeazverse_analytics_snapshots (
  id TEXT PRIMARY KEY,
  channel_id TEXT NOT NULL REFERENCES zeazverse_channels(id) ON DELETE CASCADE,
  episode_id TEXT NOT NULL DEFAULT '',
  metric_date TEXT NOT NULL,
  views INTEGER NOT NULL DEFAULT 0,
  watch_time_minutes INTEGER NOT NULL DEFAULT 0,
  average_view_duration_seconds INTEGER NOT NULL DEFAULT 0,
  subscribers_gained INTEGER NOT NULL DEFAULT 0,
  engagement INTEGER NOT NULL DEFAULT 0,
  source_json TEXT NOT NULL DEFAULT '{}',
  recorded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_zanalytics_channel ON zeazverse_analytics_snapshots(channel_id, metric_date);
CREATE TABLE IF NOT EXISTS zeazverse_workflow_runs (
  id TEXT PRIMARY KEY,
  episode_id TEXT NOT NULL REFERENCES zeazverse_episodes(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'running',
  current_state TEXT NOT NULL DEFAULT 'IDEA',
  error TEXT NOT NULL DEFAULT '',
  started_at TEXT NOT NULL,
  completed_at TEXT NOT NULL DEFAULT '',
  metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_zwf_runs_episode ON zeazverse_workflow_runs(episode_id, status);
CREATE TABLE IF NOT EXISTS zeazverse_audit_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  actor TEXT NOT NULL DEFAULT '',
  event TEXT NOT NULL,
  entity_type TEXT NOT NULL DEFAULT '',
  entity_id TEXT NOT NULL DEFAULT '',
  details_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_zaudit_ts ON zeazverse_audit_events(ts);
CREATE INDEX IF NOT EXISTS idx_zaudit_entity ON zeazverse_audit_events(entity_type, entity_id);
"""

# Episode state machine (Sec. 13). Forward transitions only; human approval
# required to leave READY_FOR_REVIEW -> APPROVED -> UPLOADING -> PRIVATE_UPLOADED.
EPISODE_STATES = (
    "IDEA",
    "SCRIPT_APPROVED",
    "ASSETS_READY",
    "RENDERING",
    "RENDERED",
    "QA_PENDING",
    "QA_PASSED",
    "READY_FOR_REVIEW",
    "APPROVED",
    "UPLOADING",
    "PRIVATE_UPLOADED",
    "PUBLISHED",
    "FAILED",
    "CANCELLED",
    "BLOCKED",
)

EPISODE_TRANSITIONS: dict[str, frozenset[str]] = {
    "IDEA": frozenset({"SCRIPT_APPROVED", "FAILED", "CANCELLED", "BLOCKED"}),
    "SCRIPT_APPROVED": frozenset({"ASSETS_READY", "FAILED", "CANCELLED", "BLOCKED"}),
    "ASSETS_READY": frozenset({"RENDERING", "FAILED", "CANCELLED", "BLOCKED"}),
    "RENDERING": frozenset({"RENDERED", "FAILED", "CANCELLED", "BLOCKED"}),
    "RENDERED": frozenset({"QA_PENDING", "FAILED", "CANCELLED", "BLOCKED"}),
    "QA_PENDING": frozenset({"QA_PASSED", "FAILED", "CANCELLED", "BLOCKED"}),
    "QA_PASSED": frozenset({"READY_FOR_REVIEW", "FAILED", "CANCELLED", "BLOCKED"}),
    "READY_FOR_REVIEW": frozenset({"APPROVED", "FAILED", "CANCELLED", "BLOCKED"}),
    "APPROVED": frozenset({"UPLOADING", "FAILED", "CANCELLED", "BLOCKED"}),
    "UPLOADING": frozenset({"PRIVATE_UPLOADED", "FAILED", "CANCELLED", "BLOCKED"}),
    "PRIVATE_UPLOADED": frozenset({"PUBLISHED", "FAILED", "CANCELLED", "BLOCKED"}),
    "PUBLISHED": frozenset(),
    "FAILED": frozenset({"IDEA", "CANCELLED", "BLOCKED"}),
    "CANCELLED": frozenset(),
    "BLOCKED": frozenset({"IDEA"}),
}

# States that require explicit human approval before leaving.
APPROVAL_GUARD_STATES = frozenset({"READY_FOR_REVIEW", "APPROVED", "UPLOADING", "PRIVATE_UPLOADED"})


def ensure_tables() -> None:
    with connect() as conn:
        conn.executescript(TABLE_SQL)


def _row(conn: Any, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    row = conn.execute(query, params).fetchone()
    return dict(row) if row else None


def _audit(
    conn: Any,
    *,
    actor: str,
    event: str,
    entity_type: str,
    entity_id: str,
    details: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        "INSERT INTO zeazverse_audit_events(ts,actor,event,entity_type,entity_id,details_json)"
        " VALUES(?,?,?,?,?,?)",
        (
            utcnow(),
            actor,
            event,
            entity_type,
            entity_id,
            json.dumps(details or {}, ensure_ascii=False),
        ),
    )


def valid_transition(current: str, target: str) -> bool:
    return target in EPISODE_TRANSITIONS.get(current, frozenset())


def requires_approval(state: str) -> bool:
    return state in APPROVAL_GUARD_STATES


# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------

def upsert_channel(channel: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    now = utcnow()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_channels("
            "id,name,handle,description,status,country,language,audience_made_for_kids,"
            "branding_hash,owner,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET name=excluded.name,handle=excluded.handle,"
            "description=excluded.description,status=excluded.status,country=excluded.country,"
            "language=excluded.language,audience_made_for_kids=excluded.audience_made_for_kids,"
            "branding_hash=excluded.branding_hash,owner=excluded.owner,updated_at=excluded.updated_at",
            (
                channel["id"], channel["name"], channel["handle"],
                channel.get("description", ""), channel.get("status", "setup"),
                channel.get("country", "TH"), channel.get("language", "en"),
                1 if channel.get("audience_made_for_kids") else 0,
                channel.get("branding_hash", ""), channel["owner"],
                channel.get("created_at", now), now,
            ),
        )
        _audit(conn, actor=channel["owner"], event="channel.upsert",
               entity_type="channel", entity_id=channel["id"],
               details={k: channel.get(k) for k in ("name", "handle", "status")})
        row = _row(conn, "SELECT * FROM zeazverse_channels WHERE id=?", (channel["id"],))
        assert row is not None
        return row


def get_channel(channel_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM zeazverse_channels WHERE id=?", (channel_id,))


def get_channel_by_handle(handle: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM zeazverse_channels WHERE handle=?", (handle,))


def list_channels(*, owner: str | None = None) -> list[dict[str, Any]]:
    ensure_tables()
    with connect() as conn:
        if owner:
            rows = conn.execute(
                "SELECT * FROM zeazverse_channels WHERE owner=? ORDER BY updated_at DESC",
                (owner,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM zeazverse_channels ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Channel integrations (YouTube OAuth, token encryption at rest)
# ---------------------------------------------------------------------------

def upsert_channel_integration(integration: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    now = utcnow()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_channel_integrations("
            "id,channel_id,provider,channel_id_external,access_token_encrypted,"
            "refresh_token_encrypted,token_expires_at,scopes,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET channel_id_external=excluded.channel_id_external,"
            "access_token_encrypted=excluded.access_token_encrypted,"
            "refresh_token_encrypted=excluded.refresh_token_encrypted,"
            "token_expires_at=excluded.token_expires_at,scopes=excluded.scopes,"
            "updated_at=excluded.updated_at",
            (
                integration["id"], integration["channel_id"],
                integration.get("provider", "youtube"),
                integration.get("channel_id_external", ""),
                integration.get("access_token_encrypted", ""),
                integration.get("refresh_token_encrypted", ""),
                integration.get("token_expires_at", ""),
                json.dumps(integration.get("scopes", []), ensure_ascii=False),
                integration.get("created_at", now), now,
            ),
        )
        row = _row(conn, "SELECT * FROM zeazverse_channel_integrations WHERE id=?", (integration["id"],))
        assert row is not None
        return row


def get_channel_integration(channel_id: str, provider: str = "youtube") -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(
            conn,
            "SELECT * FROM zeazverse_channel_integrations WHERE channel_id=? AND provider=?",
            (channel_id, provider),
        )


# ---------------------------------------------------------------------------
# Characters (canon Character Bible, Sec. 4)
# ---------------------------------------------------------------------------

def upsert_character(character: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    now = utcnow()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_characters("
            "id,name,archetype,nationality,adult,appearance,hair,wardrobe,personality,"
            "voice_profile,visual_continuity_rules,reference_assets,canonical_hash,"
            "status,owner,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET name=excluded.name,archetype=excluded.archetype,"
            "nationality=excluded.nationality,adult=excluded.adult,appearance=excluded.appearance,"
            "hair=excluded.hair,wardrobe=excluded.wardrobe,personality=excluded.personality,"
            "voice_profile=excluded.voice_profile,visual_continuity_rules=excluded.visual_continuity_rules,"
            "reference_assets=excluded.reference_assets,canonical_hash=excluded.canonical_hash,"
            "status=excluded.status,owner=excluded.owner,updated_at=excluded.updated_at",
            (
                character["id"], character["name"], character["archetype"],
                character.get("nationality", "Thai"),
                1 if character.get("adult", True) else 0,
                character.get("appearance", ""), character.get("hair", ""),
                character.get("wardrobe", ""), character.get("personality", ""),
                character.get("voice_profile", ""),
                json.dumps(character.get("visual_continuity_rules", []), ensure_ascii=False),
                json.dumps(character.get("reference_assets", []), ensure_ascii=False),
                character.get("canonical_hash", ""),
                character.get("status", "draft"), character["owner"],
                character.get("created_at", now), now,
            ),
        )
        _audit(conn, actor=character["owner"], event="character.upsert",
               entity_type="character", entity_id=character["id"],
               details={k: character.get(k) for k in ("name", "archetype", "status", "canonical_hash")})
        row = _row(conn, "SELECT * FROM zeazverse_characters WHERE id=?", (character["id"],))
        assert row is not None
        return row


def get_character(character_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM zeazverse_characters WHERE id=?", (character_id,))


def list_characters(*, owner: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    ensure_tables()
    with connect() as conn:
        query = "SELECT * FROM zeazverse_characters WHERE 1=1"
        params: list[Any] = []
        if owner:
            query += " AND owner=?"
            params.append(owner)
        if status:
            query += " AND status=?"
            params.append(status)
        query += " ORDER BY updated_at DESC"
        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]


def record_character_version(
    *,
    character_id: str,
    version: int,
    payload: dict[str, Any],
    change_reason: str,
    approved_by: str,
    approved_at: str,
) -> dict[str, Any]:
    ensure_tables()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_character_versions("
            "character_id,version,payload_json,change_reason,approved_by,approved_at,created_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (
                character_id, version,
                json.dumps(payload, ensure_ascii=False),
                change_reason, approved_by, approved_at, utcnow(),
            ),
        )
        row = _row(
            conn,
            "SELECT * FROM zeazverse_character_versions WHERE character_id=? AND version=?",
            (character_id, version),
        )
        assert row is not None
        return row


def list_character_versions(character_id: str) -> list[dict[str, Any]]:
    ensure_tables()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM zeazverse_character_versions WHERE character_id=? ORDER BY version DESC",
            (character_id,),
        ).fetchall()
        return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Character assets
# ---------------------------------------------------------------------------

def upsert_character_asset(asset: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_character_assets("
            "id,character_id,kind,name,path,sha256,width,height,duration_seconds,metadata_json,owner,created_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"  # 12 placeholders (id, character_id, kind, name, path, sha256, width, height, duration_seconds, metadata_json, owner, created_at)
            " ON CONFLICT(id) DO UPDATE SET kind=excluded.kind,name=excluded.name,path=excluded.path,"
            "sha256=excluded.sha256,width=excluded.width,height=excluded.height,"
            "duration_seconds=excluded.duration_seconds,metadata_json=excluded.metadata_json,owner=excluded.owner",
            (
                asset["id"], asset["character_id"], asset["kind"], asset["name"],
                asset["path"], asset.get("sha256", ""), int(asset.get("width", 0)),
                int(asset.get("height", 0)), float(asset.get("duration_seconds", 0)),
                json.dumps(asset.get("metadata", {}), ensure_ascii=False),
                asset.get("owner", "local"),  # <-- เพิ่ม owner ใน values
                asset.get("created_at", utcnow()),
            ),
        )
        row = _row(conn, "SELECT * FROM zeazverse_character_assets WHERE id=?", (asset["id"],))
        assert row is not None
        return row


def list_character_assets(character_id: str) -> list[dict[str, Any]]:
    ensure_tables()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM zeazverse_character_assets WHERE character_id=? ORDER BY created_at DESC",
            (character_id,),
        ).fetchall()
        return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Series
# ---------------------------------------------------------------------------

def upsert_series(series: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    now = utcnow()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_series("
            "id,channel_id,title,concept,genre,status,owner,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET title=excluded.title,concept=excluded.concept,"
            "genre=excluded.genre,status=excluded.status,owner=excluded.owner,updated_at=excluded.updated_at",
            (
                series["id"], series["channel_id"], series["title"],
                series.get("concept", ""), series.get("genre", ""),
                series.get("status", "planning"), series["owner"],
                series.get("created_at", now), now,
            ),
        )
        _audit(conn, actor=series["owner"], event="series.upsert",
               entity_type="series", entity_id=series["id"],
               details={k: series.get(k) for k in ("title", "genre", "status")})
        row = _row(conn, "SELECT * FROM zeazverse_series WHERE id=?", (series["id"],))
        assert row is not None
        return row


def get_series(series_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM zeazverse_series WHERE id=?", (series_id,))


def list_series(*, channel_id: str | None = None, owner: str | None = None) -> list[dict[str, Any]]:
    ensure_tables()
    with connect() as conn:
        query = "SELECT * FROM zeazverse_series WHERE 1=1"
        params: list[Any] = []
        if channel_id:
            query += " AND channel_id=?"
            params.append(channel_id)
        if owner:
            query += " AND owner=?"
            params.append(owner)
        query += " ORDER BY updated_at DESC"
        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Episodes (state machine, Sec. 13)
# ---------------------------------------------------------------------------

def upsert_episode(episode: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    now = utcnow()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_episodes("
            "id,series_id,channel_id,episode_number,title,concept,state,idempotency_key,"
            "script_id,storyboard_id,render_job_id,qa_report_id,approval_request_id,"
            "publication_id,owner,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET series_id=excluded.series_id,"
            "channel_id=excluded.channel_id,episode_number=excluded.episode_number,"
            "title=excluded.title,concept=excluded.concept,state=excluded.state,"
            "script_id=excluded.script_id,storyboard_id=excluded.storyboard_id,"
            "render_job_id=excluded.render_job_id,qa_report_id=excluded.qa_report_id,"
            "approval_request_id=excluded.approval_request_id,"
            "publication_id=excluded.publication_id,owner=excluded.owner,updated_at=excluded.updated_at",
            (
                episode["id"], episode["series_id"], episode["channel_id"],
                episode["episode_number"], episode["title"], episode.get("concept", ""),
                episode.get("state", "IDEA"), episode["idempotency_key"],
                episode.get("script_id", ""), episode.get("storyboard_id", ""),
                episode.get("render_job_id", ""), episode.get("qa_report_id", ""),
                episode.get("approval_request_id", ""), episode.get("publication_id", ""),
                episode["owner"], episode.get("created_at", now), now,
            ),
        )
        _audit(conn, actor=episode["owner"], event="episode.upsert",
               entity_type="episode", entity_id=episode["id"],
               details={k: episode.get(k) for k in ("title", "state", "series_id")})
        row = _row(conn, "SELECT * FROM zeazverse_episodes WHERE id=?", (episode["id"],))
        assert row is not None
        return row


def get_episode(episode_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM zeazverse_episodes WHERE id=?", (episode_id,))


def get_episode_by_idempotency_key(idempotency_key: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(
            conn,
            "SELECT * FROM zeazverse_episodes WHERE idempotency_key=?",
            (idempotency_key,),
        )


def list_episodes(
    *,
    series_id: str | None = None,
    channel_id: str | None = None,
    state: str | None = None,
    owner: str | None = None,
) -> list[dict[str, Any]]:
    ensure_tables()
    with connect() as conn:
        query = "SELECT * FROM zeazverse_episodes WHERE 1=1"
        params: list[Any] = []
        if series_id:
            query += " AND series_id=?"
            params.append(series_id)
        if channel_id:
            query += " AND channel_id=?"
            params.append(channel_id)
        if state:
            query += " AND state=?"
            params.append(state)
        if owner:
            query += " AND owner=?"
            params.append(owner)
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]


def transition_episode(
    *,
    episode_id: str,
    target_state: str,
    actor: str,
    justification: str = "",
) -> dict[str, Any]:
    """อัปเดต state ของ episode ตาม state machine (Sec. 13).

    รัฐ READY_FOR_REVIEW / APPROVED / UPLOADING / PRIVATE_UPLOADED ต้องมี
   การอนุมัติจากมนุษย์ก่อนจึงจะถัดไปได้ (ตรวจจาก approval_requests).
    """
    ensure_tables()
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = _row(conn, "SELECT * FROM zeazverse_episodes WHERE id=?", (episode_id,))
        if row is None:
            raise ValueError(f"episode not found: {episode_id}")
        current = row["state"]
        if current == target_state:
            conn.execute("COMMIT")
            return dict(row)
        if not valid_transition(current, target_state):
            raise ValueError(
                f"invalid episode state transition {current} -> {target_state}"
            )
        if target_state in APPROVAL_GUARD_STATES:
            approval = _row(
                conn,
                "SELECT * FROM zeazverse_approval_requests WHERE episode_id=? AND decision='approved'",
                (episode_id,),
            )
            if approval is None:
                raise ValueError(
                    f"human approval required before entering state {target_state}"
                )
        now = utcnow()
        conn.execute(
            "UPDATE zeazverse_episodes SET state=?, updated_at=? WHERE id=?",
            (target_state, now, episode_id),
        )
        _audit(
            conn, actor=actor, event="episode.transition",
            entity_type="episode", entity_id=episode_id,
            details={"from": current, "to": target_state, "justification": justification},
        )
        updated = _row(conn, "SELECT * FROM zeazverse_episodes WHERE id=?", (episode_id,))
        conn.execute("COMMIT")
        assert updated is not None
        return dict(updated)


# ---------------------------------------------------------------------------
# Scripts
# ---------------------------------------------------------------------------

def upsert_script(script: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_scripts("
            "id,episode_id,title,content,language,thai_localization,version,status,"
            "owner,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET title=excluded.title,content=excluded.content,"
            "language=excluded.language,thai_localization=excluded.thai_localization,"
            "version=excluded.version,status=excluded.status,owner=excluded.owner,"
            "updated_at=excluded.updated_at",
            (
                script["id"], script["episode_id"], script["title"],
                script.get("content", ""), script.get("language", "en"),
                json.dumps(script.get("thai_localization", {}), ensure_ascii=False),
                int(script.get("version", 1)), script.get("status", "draft"),
                script["owner"], script.get("created_at", utcnow()), utcnow(),
            ),
        )
        row = _row(conn, "SELECT * FROM zeazverse_scripts WHERE id=?", (script["id"],))
        assert row is not None
        return row


def get_script(script_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM zeazverse_scripts WHERE id=?", (script_id,))


# ---------------------------------------------------------------------------
# Storyboards
# ---------------------------------------------------------------------------

def upsert_storyboard(storyboard: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_storyboards("
            "id,episode_id,title,scenes_json,version,status,owner,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET title=excluded.title,scenes_json=excluded.scenes_json,"
            "version=excluded.version,status=excluded.status,owner=excluded.owner,"
            "updated_at=excluded.updated_at",
            (
                storyboard["id"], storyboard["episode_id"], storyboard["title"],
                json.dumps(storyboard.get("scenes", []), ensure_ascii=False),
                int(storyboard.get("version", 1)), storyboard.get("status", "draft"),
                storyboard["owner"], storyboard.get("created_at", utcnow()), utcnow(),
            ),
        )
        row = _row(conn, "SELECT * FROM zeazverse_storyboards WHERE id=?", (storyboard["id"],))
        assert row is not None
        return row


def get_storyboard(storyboard_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM zeazverse_storyboards WHERE id=?", (storyboard_id,))


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------

def upsert_scene(scene: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_scenes("
            "id,storyboard_id,episode_id,scene_number,time_start_seconds,time_end_seconds,"
            "characters_json,environment,subject_action,camera_framing,camera_movement,"
            "lighting,dialogue,audio,positive_prompt,negative_prompt,"
            "first_frame_continuity,last_frame_continuity,generation_model,model_settings_json,"
            "expected_output,qa_checks_json,status,owner,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET storyboard_id=excluded.storyboard_id,"
            "episode_id=excluded.episode_id,scene_number=excluded.scene_number,"
            "time_start_seconds=excluded.time_start_seconds,time_end_seconds=excluded.time_end_seconds,"
            "characters_json=excluded.characters_json,environment=excluded.environment,"
            "subject_action=excluded.subject_action,camera_framing=excluded.camera_framing,"
            "camera_movement=excluded.camera_movement,lighting=excluded.lighting,"
            "dialogue=excluded.dialogue,audio=excluded.audio,positive_prompt=excluded.positive_prompt,"
            "negative_prompt=excluded.negative_prompt,first_frame_continuity=excluded.first_frame_continuity,"
            "last_frame_continuity=excluded.last_frame_continuity,generation_model=excluded.generation_model,"
            "model_settings_json=excluded.model_settings_json,expected_output=excluded.expected_output,"
            "qa_checks_json=excluded.qa_checks_json,status=excluded.status,owner=excluded.owner,"
            "updated_at=excluded.updated_at",
            (
                scene["id"], scene["storyboard_id"], scene["episode_id"],
                scene["scene_number"], int(scene.get("time_start_seconds", 0)),
                int(scene.get("time_end_seconds", 30)),
                json.dumps(scene.get("characters", []), ensure_ascii=False),
                scene.get("environment", ""), scene.get("subject_action", ""),
                scene.get("camera_framing", ""), scene.get("camera_movement", ""),
                scene.get("lighting", ""), scene.get("dialogue", ""), scene.get("audio", ""),
                scene.get("positive_prompt", ""), scene.get("negative_prompt", ""),
                scene.get("first_frame_continuity", ""), scene.get("last_frame_continuity", ""),
                scene.get("generation_model", ""),
                json.dumps(scene.get("model_settings", {}), ensure_ascii=False),
                scene.get("expected_output", ""),
                json.dumps(scene.get("qa_checks", []), ensure_ascii=False),
                scene.get("status", "draft"), scene["owner"],
                scene.get("created_at", utcnow()), utcnow(),
            ),
        )
        row = _row(conn, "SELECT * FROM zeazverse_scenes WHERE id=?", (scene["id"],))
        assert row is not None
        return row


def get_scene(scene_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM zeazverse_scenes WHERE id=?", (scene_id,))


# ---------------------------------------------------------------------------
# Generation jobs & artifacts
# ---------------------------------------------------------------------------

def upsert_generation_job(job: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_generation_jobs("
            "id,scene_id,provider,model,status,input_hash,output_path,error,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET provider=excluded.provider,model=excluded.model,"
            "status=excluded.status,input_hash=excluded.input_hash,output_path=excluded.output_path,"
            "error=excluded.error,updated_at=excluded.updated_at",
            (
                job["id"], job["scene_id"], job.get("provider", ""), job.get("model", ""),
                job.get("status", "queued"), job.get("input_hash", ""),
                job.get("output_path", ""), job.get("error", ""),
                job.get("created_at", utcnow()), utcnow(),
            ),
        )
        row = _row(conn, "SELECT * FROM zeazverse_generation_jobs WHERE id=?", (job["id"],))
        assert row is not None
        return row


def get_generation_job(job_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM zeazverse_generation_jobs WHERE id=?", (job_id,))


def upsert_generation_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_generation_artifacts("
            "id,generation_job_id,kind,path,sha256,width,height,duration_seconds,metadata_json,created_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET kind=excluded.kind,path=excluded.path,"
            "sha256=excluded.sha256,width=excluded.width,height=excluded.height,"
            "duration_seconds=excluded.duration_seconds,metadata_json=excluded.metadata_json",
            (
                artifact["id"], artifact["generation_job_id"], artifact["kind"],
                artifact["path"], artifact.get("sha256", ""), int(artifact.get("width", 0)),
                int(artifact.get("height", 0)), float(artifact.get("duration_seconds", 0)),
                json.dumps(artifact.get("metadata", {}), ensure_ascii=False),
                artifact.get("created_at", utcnow()),
            ),
        )
        row = _row(conn, "SELECT * FROM zeazverse_generation_artifacts WHERE id=?", (artifact["id"],))
        assert row is not None
        return row


# ---------------------------------------------------------------------------
# QA reports
# ---------------------------------------------------------------------------

def upsert_qa_report(report: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_qa_reports("
            "id,episode_id,passed,checks_json,defects_json,reviewer,reviewed_at,notes,created_at)"
            " VALUES(?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET passed=excluded.passed,checks_json=excluded.checks_json,"
            "defects_json=excluded.defects_json,reviewer=excluded.reviewer,reviewed_at=excluded.reviewed_at,"
            "notes=excluded.notes,created_at=excluded.created_at",
            (
                report["id"], report["episode_id"],
                1 if report.get("passed") else 0,
                json.dumps(report.get("checks", []), ensure_ascii=False),
                json.dumps(report.get("defects", []), ensure_ascii=False),
                report.get("reviewer", ""), report.get("reviewed_at", ""),
                report.get("notes", ""), report.get("created_at", utcnow()),
            ),
        )
        row = _row(conn, "SELECT * FROM zeazverse_qa_reports WHERE id=?", (report["id"],))
        assert row is not None
        return row


def get_qa_report(qa_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM zeazverse_qa_reports WHERE id=?", (qa_id,))


# ---------------------------------------------------------------------------
# Approval requests
# ---------------------------------------------------------------------------

def upsert_approval_request(request: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_approval_requests("
            "id,episode_id,requested_by,requested_at,decided_by,decided_at,decision,"
            "justification,idempotency_key,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET requested_by=excluded.requested_by,"
            "requested_at=excluded.requested_at,decided_by=excluded.decided_by,"
            "decided_at=excluded.decided_at,decision=excluded.decision,"
            "justification=excluded.justification,updated_at=excluded.updated_at",
            (
                request["id"], request["episode_id"], request.get("requested_by", ""),
                request.get("requested_at", utcnow()), request.get("decided_by", ""),
                request.get("decided_at", ""), request.get("decision", "pending"),
                request.get("justification", ""), request["idempotency_key"],
                request.get("created_at", utcnow()), utcnow(),
            ),
        )
        row = _row(conn, "SELECT * FROM zeazverse_approval_requests WHERE id=?", (request["id"],))
        assert row is not None
        return row


def get_approval_request(approval_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM zeazverse_approval_requests WHERE id=?", (approval_id,))


def get_approval_request_by_idempotency_key(idempotency_key: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(
            conn,
            "SELECT * FROM zeazverse_approval_requests WHERE idempotency_key=?",
            (idempotency_key,),
        )


# ---------------------------------------------------------------------------
# Publications
# ---------------------------------------------------------------------------

def upsert_publication(publication: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_publications("
            "id,episode_id,platform,state,idempotency_key,owner,external_id,external_url,"
            "title,description,tags_json,playlist,privacy,schedule_at,published_at,"
            "error,metadata_json,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET platform=excluded.platform,state=excluded.state,"
            "external_id=excluded.external_id,external_url=excluded.external_url,"
            "title=excluded.title,description=excluded.description,tags_json=excluded.tags_json,"
            "playlist=excluded.playlist,privacy=excluded.privacy,schedule_at=excluded.schedule_at,"
            "published_at=excluded.published_at,error=excluded.error,"
            "metadata_json=excluded.metadata_json,updated_at=excluded.updated_at",
            (
                publication["id"], publication["episode_id"],
                publication.get("platform", "youtube"), publication.get("state", "IDEA"),
                publication["idempotency_key"], publication.get("owner", "local"),
                publication.get("external_id", ""),
                publication.get("external_url", ""), publication.get("title", ""),
                publication.get("description", ""),
                json.dumps(publication.get("tags", []), ensure_ascii=False),
                publication.get("playlist", ""), publication.get("privacy", "private"),
                publication.get("schedule_at", ""), publication.get("published_at", ""),
                publication.get("error", ""),
                json.dumps(publication.get("metadata", {}), ensure_ascii=False),
                publication.get("created_at", utcnow()), utcnow(),
            ),
        )
        row = _row(conn, "SELECT * FROM zeazverse_publications WHERE id=?", (publication["id"],))
        assert row is not None
        return row


def get_publication(publication_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM zeazverse_publications WHERE id=?", (publication_id,))


def get_publication_by_idempotency_key(idempotency_key: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(
            conn,
            "SELECT * FROM zeazverse_publications WHERE idempotency_key=?",
            (idempotency_key,),
        )


# ---------------------------------------------------------------------------
# Analytics snapshots
# ---------------------------------------------------------------------------

def upsert_analytics_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_analytics_snapshots("
            "id,channel_id,episode_id,metric_date,views,watch_time_minutes,"
            "average_view_duration_seconds,subscribers_gained,engagement,source_json,recorded_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET views=excluded.views,watch_time_minutes=excluded.watch_time_minutes,"
            "average_view_duration_seconds=excluded.average_view_duration_seconds,"
            "subscribers_gained=excluded.subscribers_gained,engagement=excluded.engagement,"
            "source_json=excluded.source_json,recorded_at=excluded.recorded_at",
            (
                snapshot["id"], snapshot["channel_id"], snapshot.get("episode_id", ""),
                snapshot["metric_date"], int(snapshot.get("views", 0)),
                int(snapshot.get("watch_time_minutes", 0)),
                int(snapshot.get("average_view_duration_seconds", 0)),
                int(snapshot.get("subscribers_gained", 0)), int(snapshot.get("engagement", 0)),
                json.dumps(snapshot.get("source", {}), ensure_ascii=False),
                snapshot.get("recorded_at", utcnow()),
            ),
        )
        row = _row(conn, "SELECT * FROM zeazverse_analytics_snapshots WHERE id=?", (snapshot["id"],))
        assert row is not None
        return row


# ---------------------------------------------------------------------------
# Workflow runs
# ---------------------------------------------------------------------------

def upsert_workflow_run(run: dict[str, Any]) -> dict[str, Any]:
    ensure_tables()
    with connect() as conn:
        conn.execute(
            "INSERT INTO zeazverse_workflow_runs("
            "id,episode_id,status,current_state,error,started_at,completed_at,metadata_json)"
            " VALUES(?,?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET status=excluded.status,current_state=excluded.current_state,"
            "error=excluded.error,completed_at=excluded.completed_at,metadata_json=excluded.metadata_json",
            (
                run["id"], run["episode_id"], run.get("status", "running"),
                run.get("current_state", "IDEA"), run.get("error", ""),
                run.get("started_at", utcnow()), run.get("completed_at", ""),
                json.dumps(run.get("metadata", {}), ensure_ascii=False),
            ),
        )
        row = _row(conn, "SELECT * FROM zeazverse_workflow_runs WHERE id=?", (run["id"],))
        assert row is not None
        return row


def get_workflow_run(run_id: str) -> dict[str, Any] | None:
    ensure_tables()
    with connect() as conn:
        return _row(conn, "SELECT * FROM zeazverse_workflow_runs WHERE id=?", (run_id,))


def list_workflow_runs(*, episode_id: str | None = None) -> list[dict[str, Any]]:
    ensure_tables()
    with connect() as conn:
        if episode_id:
            rows = conn.execute(
                "SELECT * FROM zeazverse_workflow_runs WHERE episode_id=? ORDER BY started_at DESC",
                (episode_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM zeazverse_workflow_runs ORDER BY started_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Audit events
# ---------------------------------------------------------------------------

def list_audit_events(
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    ensure_tables()
    with connect() as conn:
        query = "SELECT * FROM zeazverse_audit_events WHERE 1=1"
        params: list[Any] = []
        if entity_type:
            query += " AND entity_type=?"
            params.append(entity_type)
        if entity_id:
            query += " AND entity_id=?"
            params.append(entity_id)
        query += " ORDER BY ts DESC LIMIT ?"
        params.append(max(1, min(limit, 1000)))
        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]
