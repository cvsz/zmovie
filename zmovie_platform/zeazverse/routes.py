"""ZEAZVERSE REST API (Sec. 14-15).

Endpoints are mounted under ``/api/v2/zeazverse`` by ``main.py``. All
mutating endpoints require authentication (``current_actor``), write audit
events, and enforce the episode state machine (Sec. 13) where applicable.

Read endpoints return domain records; they never fabricate external provider
responses (YouTube, render models, etc.).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..api_routes import current_actor, settings
from ..audit import write as audit
from ..models import utcnow
from ..storage import connect
from ..zeazverse.store import (
    APPROVAL_GUARD_STATES,
    EPISODE_STATES,
    EPISODE_TRANSITIONS,
    get_approval_request,
    get_approval_request_by_idempotency_key,
    get_channel,
    get_channel_by_handle,
    get_channel_integration,
    get_character,
    get_episode,
    get_episode_by_idempotency_key,
    get_generation_job,
    get_publication,
    get_publication_by_idempotency_key,
    get_qa_report,
    get_scene,
    get_script,
    get_series,
    get_storyboard,
    list_analytics_snapshots,
    list_approval_requests,
    list_audit_events,
    list_channels,
    list_character_assets,
    list_character_versions,
    list_characters,
    list_episodes,
    list_publications,
    list_scenes,
    list_series,
    list_workflow_runs,
    record_character_version,
    transition_episode,
    upsert_analytics_snapshot,
    upsert_approval_request,
    upsert_channel,
    upsert_character,
    upsert_character_asset,
    upsert_episode,
    upsert_generation_artifact,
    upsert_generation_job,
    upsert_publication,
    upsert_qa_report,
    upsert_scene,
    upsert_script,
    upsert_series,
    upsert_storyboard,
    upsert_workflow_run,
    valid_transition,
)

router = APIRouter(prefix="/api/v2/zeazverse", tags=["zeazverse"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ChannelRequest(BaseModel):
    id: str
    name: str
    handle: str
    description: str = ""
    status: str = "setup"
    country: str = "TH"
    language: str = "en"
    audience_made_for_kids: bool = False
    branding_hash: str = ""
    owner: str = "local"


class CharacterRequest(BaseModel):
    id: str
    name: str
    archetype: str
    nationality: str = "Thai"
    adult: bool = True
    appearance: str = ""
    hair: str = ""
    wardrobe: str = ""
    personality: str = ""
    voice_profile: str = ""
    visual_continuity_rules: list[str] = Field(default_factory=list)
    reference_assets: list[str] = Field(default_factory=list)
    canonical_hash: str = ""
    status: str = "draft"
    owner: str = "local"


class CharacterVersionRequest(BaseModel):
    character_id: str
    version: int
    payload: dict[str, Any] = Field(default_factory=dict)
    change_reason: str = ""
    approved_by: str = "local"
    approved_at: str = Field(default_factory=utcnow)


class CharacterAssetRequest(BaseModel):
    id: str
    character_id: str
    kind: str
    name: str
    path: str
    sha256: str = ""
    width: int = 0
    height: int = 0
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class SeriesRequest(BaseModel):
    id: str
    channel_id: str
    title: str
    concept: str = ""
    genre: str = ""
    status: str = "planning"
    owner: str = "local"


class EpisodeRequest(BaseModel):
    id: str
    series_id: str
    channel_id: str
    episode_number: int
    title: str
    concept: str = ""
    state: str = "IDEA"
    idempotency_key: str = ""
    script_id: str = ""
    storyboard_id: str = ""
    render_job_id: str = ""
    qa_report_id: str = ""
    approval_request_id: str = ""
    publication_id: str = ""
    owner: str = "local"


class TransitionRequest(BaseModel):
    target_state: str
    justification: str = ""


class ScriptRequest(BaseModel):
    id: str
    episode_id: str
    title: str
    content: str = ""
    language: str = "en"
    thai_localization: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    status: str = "draft"
    owner: str = "local"


class StoryboardRequest(BaseModel):
    id: str
    episode_id: str
    title: str
    scenes: list[dict[str, Any]] = Field(default_factory=list)
    version: int = 1
    status: str = "draft"
    owner: str = "local"


class SceneRequest(BaseModel):
    id: str
    storyboard_id: str
    episode_id: str
    scene_number: int
    time_start_seconds: int = 0
    time_end_seconds: int = 30
    characters: list[str] = Field(default_factory=list)
    environment: str = ""
    subject_action: str = ""
    camera_framing: str = ""
    camera_movement: str = ""
    lighting: str = ""
    dialogue: str = ""
    audio: str = ""
    positive_prompt: str = ""
    negative_prompt: str = ""
    first_frame_continuity: str = ""
    last_frame_continuity: str = ""
    generation_model: str = ""
    model_settings: dict[str, Any] = Field(default_factory=dict)
    expected_output: str = ""
    qa_checks: list[str] = Field(default_factory=list)
    status: str = "draft"
    owner: str = "local"


class GenerationJobRequest(BaseModel):
    id: str
    scene_id: str
    provider: str = ""
    model: str = ""
    status: str = "queued"
    input_hash: str = ""
    output_path: str = ""
    error: str = ""


class GenerationArtifactRequest(BaseModel):
    id: str
    generation_job_id: str
    kind: str
    path: str
    sha256: str = ""
    width: int = 0
    height: int = 0
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class QAReportRequest(BaseModel):
    id: str
    episode_id: str
    passed: bool = False
    checks: list[dict[str, Any]] = Field(default_factory=list)
    defects: list[dict[str, Any]] = Field(default_factory=list)
    reviewer: str = ""
    reviewed_at: str = ""
    notes: str = ""


class ApprovalRequestRequest(BaseModel):
    id: str
    episode_id: str
    requested_by: str = "local"
    requested_at: str = Field(default_factory=utcnow)
    decided_by: str = ""
    decided_at: str = ""
    decision: str = "pending"
    justification: str = ""
    idempotency_key: str = ""


class PublicationRequest(BaseModel):
    id: str
    episode_id: str
    platform: str = "youtube"
    state: str = "IDEA"
    idempotency_key: str = ""
    external_id: str = ""
    external_url: str = ""
    title: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    playlist: str = ""
    privacy: str = "private"
    schedule_at: str = ""
    published_at: str = ""
    error: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyticsSnapshotRequest(BaseModel):
    id: str
    channel_id: str
    episode_id: str = ""
    metric_date: str = ""
    views: int = 0
    watch_time_minutes: int = 0
    average_view_duration_seconds: int = 0
    subscribers_gained: int = 0
    engagement: int = 0
    source: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunRequest(BaseModel):
    id: str
    episode_id: str
    status: str = "running"
    current_state: str = "IDEA"
    error: str = ""
    started_at: str = Field(default_factory=utcnow)
    completed_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------

@router.get("/channels")
def list_channels_endpoint(
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    owner = None if actor.get("role") == "admin" else actor["username"]
    return {"items": list_channels(owner=owner)}


@router.post("/channels")
def create_channel(
    payload: ChannelRequest, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    if payload.handle != payload.handle.lstrip("@"):
        payload.handle = payload.handle.lstrip("@")
    if get_channel_by_handle(payload.handle) is not None:
        raise HTTPException(status_code=409, detail="channel handle already exists")
    channel = payload.model_dump()
    channel["owner"] = actor["username"]
    result = upsert_channel(channel)
    audit("zeazverse.channel.create", actor=actor["username"], entity_type="channel", entity_id=result["id"])
    return {"channel": result}


@router.get("/channels/{channel_id}")
def get_channel_endpoint(
    channel_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    channel = get_channel(channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="channel not found")
    if settings.auth_enabled and actor.get("role") != "admin" and channel["owner"] != actor["username"]:
        raise HTTPException(status_code=403, detail="channel access denied")
    return {"channel": channel}


@router.get("/channels/{channel_id}/integration")
def get_channel_integration_endpoint(
    channel_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    channel = get_channel(channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="channel not found")
    if settings.auth_enabled and actor.get("role") != "admin" and channel["owner"] != actor["username"]:
        raise HTTPException(status_code=403, detail="channel access denied")
    integration = get_channel_integration(channel_id)
    return {"integration": integration}


# ---------------------------------------------------------------------------
# Characters (Character Bible, Sec. 4)
# ---------------------------------------------------------------------------

@router.get("/characters")
def list_characters_endpoint(
    owner: str | None = None,
    status: str | None = None,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    effective_owner = None if actor.get("role") == "admin" else (owner or actor["username"])
    return {"items": list_characters(owner=effective_owner, status=status)}


@router.post("/characters")
def create_character(
    payload: CharacterRequest, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    character = payload.model_dump()
    character["owner"] = actor["username"]
    result = upsert_character(character)
    audit("zeazverse.character.create", actor=actor["username"], entity_type="character", entity_id=result["id"])
    return {"character": result}


@router.get("/characters/{character_id}")
def get_character_endpoint(
    character_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    character = get_character(character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="character not found")
    if settings.auth_enabled and actor.get("role") != "admin" and character["owner"] != actor["username"]:
        raise HTTPException(status_code=403, detail="character access denied")
    return {"character": character}


@router.post("/characters/{character_id}/versions")
def create_character_version(
    character_id: str,
    payload: CharacterVersionRequest,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    character = get_character(character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="character not found")
    if settings.auth_enabled and actor.get("role") != "admin" and character["owner"] != actor["username"]:
        raise HTTPException(status_code=403, detail="character access denied")
    result = record_character_version(
        character_id=character_id,
        version=payload.version,
        payload=payload.payload,
        change_reason=payload.change_reason,
        approved_by=payload.approved_by or actor["username"],
        approved_at=payload.approved_at,
    )
    audit(
        "zeazverse.character.version",
        actor=actor["username"],
        entity_type="character",
        entity_id=character_id,
        details={"version": payload.version, "change_reason": payload.change_reason},
    )
    return {"version": result}


@router.get("/characters/{character_id}/versions")
def list_character_versions_endpoint(
    character_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    character = get_character(character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="character not found")
    if settings.auth_enabled and actor.get("role") != "admin" and character["owner"] != actor["username"]:
        raise HTTPException(status_code=403, detail="character access denied")
    return {"items": list_character_versions(character_id)}


@router.post("/characters/{character_id}/assets")
def create_character_asset(
    character_id: str,
    payload: CharacterAssetRequest,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    character = get_character(character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="character not found")
    if settings.auth_enabled and actor.get("role") != "admin" and character["owner"] != actor["username"]:
        raise HTTPException(status_code=403, detail="character access denied")
    asset = payload.model_dump()
    asset["character_id"] = character_id
    result = upsert_character_asset(asset)
    audit("zeazverse.character.asset", actor=actor["username"], entity_type="character_asset", entity_id=result["id"])
    return {"asset": result}


@router.get("/characters/{character_id}/assets")
def list_character_assets_endpoint(
    character_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    character = get_character(character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="character not found")
    if settings.auth_enabled and actor.get("role") != "admin" and character["owner"] != actor["username"]:
        raise HTTPException(status_code=403, detail="character access denied")
    return {"items": list_character_assets(character_id)}


# ---------------------------------------------------------------------------
# Series
# ---------------------------------------------------------------------------

@router.get("/series")
def list_series_endpoint(
    channel_id: str | None = None,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    owner = None if actor.get("role") == "admin" else actor["username"]
    return {"items": list_series(channel_id=channel_id, owner=owner)}


@router.post("/series")
def create_series(
    payload: SeriesRequest, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    channel = get_channel(payload.channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="channel not found")
    if settings.auth_enabled and actor.get("role") != "admin" and channel["owner"] != actor["username"]:
        raise HTTPException(status_code=403, detail="channel access denied")
    series = payload.model_dump()
    series["owner"] = actor["username"]
    result = upsert_series(series)
    audit("zeazverse.series.create", actor=actor["username"], entity_type="series", entity_id=result["id"])
    return {"series": result}


@router.get("/series/{series_id}")
def get_series_endpoint(
    series_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    series = get_series(series_id)
    if series is None:
        raise HTTPException(status_code=404, detail="series not found")
    channel = get_channel(series["channel_id"])
    if settings.auth_enabled and actor.get("role") != "admin" and channel is not None and channel["owner"] != actor["username"]:
        raise HTTPException(status_code=403, detail="series access denied")
    return {"series": series}


# ---------------------------------------------------------------------------
# Episodes (state machine, Sec. 13)
# ---------------------------------------------------------------------------

@router.get("/episodes")
def list_episodes_endpoint(
    series_id: str | None = None,
    channel_id: str | None = None,
    state: str | None = None,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    owner = None if actor.get("role") == "admin" else actor["username"]
    return {"items": list_episodes(series_id=series_id, channel_id=channel_id, state=state, owner=owner)}


@router.post("/episodes")
def create_episode(
    payload: EpisodeRequest, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    if payload.state not in EPISODE_STATES:
        raise HTTPException(status_code=400, detail=f"invalid state: {payload.state}")
    series = get_series(payload.series_id)
    if series is None:
        raise HTTPException(status_code=404, detail="series not found")
    channel = get_channel(series["channel_id"])
    if settings.auth_enabled and actor.get("role") != "admin" and channel is not None and channel["owner"] != actor["username"]:
        raise HTTPException(status_code=403, detail="series access denied")
    if get_episode_by_idempotency_key(payload.idempotency_key or payload.id) is not None:
        raise HTTPException(status_code=409, detail="episode idempotency key already exists")
    episode = payload.model_dump()
    episode["owner"] = actor["username"]
    result = upsert_episode(episode)
    audit("zeazverse.episode.create", actor=actor["username"], entity_type="episode", entity_id=result["id"])
    return {"episode": result}


@router.get("/episodes/{episode_id}")
def get_episode_endpoint(
    episode_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    episode = get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")
    series = get_series(episode["series_id"])
    channel = get_channel(series["channel_id"]) if series else None
    if settings.auth_enabled and actor.get("role") != "admin" and channel is not None and channel["owner"] != actor["username"]:
        raise HTTPException(status_code=403, detail="episode access denied")
    return {"episode": episode}


@router.post("/episodes/{episode_id}/transition")
def transition_episode_endpoint(
    episode_id: str,
    payload: TransitionRequest,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    episode = get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")
    series = get_series(episode["series_id"])
    channel = get_channel(series["channel_id"]) if series else None
    if settings.auth_enabled and actor.get("role") != "admin" and channel is not None and channel["owner"] != actor["username"]:
        raise HTTPException(status_code=403, detail="episode access denied")
    if not valid_transition(episode["state"], payload.target_state):
        raise HTTPException(
            status_code=409,
            detail={"message": "invalid transition", "from": episode["state"], "to": payload.target_state},
        )
    if payload.target_state in APPROVAL_GUARD_STATES:
        approval = get_approval_request(episode["approval_request_id"]) if episode.get("approval_request_id") else None
        if approval is None or approval.get("decision") != "approved":
            raise HTTPException(
                status_code=403,
                detail={"message": "human approval required before entering state", "state": payload.target_state},
            )
    result = transition_episode(
        episode_id=episode_id,
        target_state=payload.target_state,
        actor=actor["username"],
        justification=payload.justification,
    )
    audit(
        "zeazverse.episode.transition",
        actor=actor["username"],
        entity_type="episode",
        entity_id=episode_id,
        details={"from": episode["state"], "to": payload.target_state, "justification": payload.justification},
    )
    return {"episode": result}


@router.get("/episodes/{episode_id}/scripts")
def get_episode_scripts_endpoint(
    episode_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    episode = get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")
    return {"items": [] if not episode.get("script_id") else [get_script(episode["script_id"])]}


@router.post("/episodes/{episode_id}/scripts")
def create_episode_script(
    episode_id: str,
    payload: ScriptRequest,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    episode = get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")
    script = payload.model_dump()
    script["episode_id"] = episode_id
    script["owner"] = actor["username"]
    result = upsert_script(script)
    # Advance episode to SCRIPT_APPROVED only when status says so; otherwise keep IDEA.
    if script.get("status") == "approved":
        transition_episode(
            episode_id=episode_id, target_state="SCRIPT_APPROVED",
            actor=actor["username"], justification="script approved",
        )
    audit("zeazverse.script.create", actor=actor["username"], entity_type="script", entity_id=result["id"])
    return {"script": result}


@router.get("/episodes/{episode_id}/storyboards")
def get_episode_storyboards_endpoint(
    episode_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    episode = get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")
    return {"items": [] if not episode.get("storyboard_id") else [get_storyboard(episode["storyboard_id"])]}


@router.post("/episodes/{episode_id}/storyboards")
def create_episode_storyboard(
    episode_id: str,
    payload: StoryboardRequest,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    episode = get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")
    storyboard = payload.model_dump()
    storyboard["episode_id"] = episode_id
    storyboard["owner"] = actor["username"]
    result = upsert_storyboard(storyboard)
    if storyboard.get("status") == "approved":
        transition_episode(
            episode_id=episode_id, target_state="ASSETS_READY",
            actor=actor["username"], justification="storyboard approved",
        )
    audit("zeazverse.storyboard.create", actor=actor["username"], entity_type="storyboard", entity_id=result["id"])
    return {"storyboard": result}


# ---------------------------------------------------------------------------
# Scenes (Sec. 8 scene prompt contract)
# ---------------------------------------------------------------------------

@router.get("/storyboards/{storyboard_id}/scenes")
def list_storyboard_scenes_endpoint(
    storyboard_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    storyboard = get_storyboard(storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="storyboard not found")
    return {"items": list_scenes(storyboard_id=storyboard_id)}


@router.post("/scenes")
def create_scene(
    payload: SceneRequest, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    scene = payload.model_dump()
    scene["owner"] = actor["username"]
    result = upsert_scene(scene)
    audit("zeazverse.scene.create", actor=actor["username"], entity_type="scene", entity_id=result["id"])
    return {"scene": result}


@router.get("/scenes/{scene_id}")
def get_scene_endpoint(
    scene_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    scene = get_scene(scene_id)
    if scene is None:
        raise HTTPException(status_code=404, detail="scene not found")
    return {"scene": scene}


# ---------------------------------------------------------------------------
# Generation jobs & artifacts (Sec. 9 model adapters; mock-safe)
# ---------------------------------------------------------------------------

@router.post("/generation-jobs")
def create_generation_job(
    payload: GenerationJobRequest, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    job = payload.model_dump()
    job["owner"] = actor["username"]
    result = upsert_generation_job(job)
    audit("zeazverse.generation_job.create", actor=actor["username"], entity_type="generation_job", entity_id=result["id"])
    return {"job": result}


@router.get("/generation-jobs/{job_id}")
def get_generation_job_endpoint(
    job_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    job = get_generation_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="generation job not found")
    return {"job": job}


@router.post("/generation-artifacts")
def create_generation_artifact(
    payload: GenerationArtifactRequest, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    artifact = payload.model_dump()
    result = upsert_generation_artifact(artifact)
    audit("zeazverse.generation_artifact.create", actor=actor["username"], entity_type="generation_artifact", entity_id=result["id"])
    return {"artifact": result}


# ---------------------------------------------------------------------------
# QA reports (Sec. 12)
# ---------------------------------------------------------------------------

@router.post("/qa-reports")
def create_qa_report(
    payload: QAReportRequest, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    report = payload.model_dump()
    report["owner"] = actor["username"]
    result = upsert_qa_report(report)
    audit("zeazverse.qa_report.create", actor=actor["username"], entity_type="qa_report", entity_id=result["id"])
    return {"qa_report": result}


@router.get("/qa-reports/{qa_id}")
def get_qa_report_endpoint(
    qa_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    report = get_qa_report(qa_id)
    if report is None:
        raise HTTPException(status_code=404, detail="qa report not found")
    return {"qa_report": report}


# ---------------------------------------------------------------------------
# Approval requests (Sec. 13 human approval)
# ---------------------------------------------------------------------------

@router.post("/approval-requests")
def create_approval_request(
    payload: ApprovalRequestRequest, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    episode = get_episode(payload.episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")
    if get_approval_request_by_idempotency_key(payload.idempotency_key or payload.id) is not None:
        raise HTTPException(status_code=409, detail="approval idempotency key already exists")
    req = payload.model_dump()
    req["owner"] = actor["username"]
    result = upsert_approval_request(req)
    # Link approval request id onto episode so transitions can verify it.
    if not episode.get("approval_request_id"):
        with connect() as conn:
            conn.execute(
                "UPDATE zeazverse_episodes SET approval_request_id=?, updated_at=? WHERE id=?",
                (result["id"], utcnow(), payload.episode_id),
            )
    audit("zeazverse.approval_request.create", actor=actor["username"], entity_type="approval_request", entity_id=result["id"])
    return {"approval_request": result}


@router.get("/approval-requests/{approval_id}")
def get_approval_request_endpoint(
    approval_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    req = get_approval_request(approval_id)
    if req is None:
        raise HTTPException(status_code=404, detail="approval request not found")
    return {"approval_request": req}


@router.get("/approval-requests")
def list_approval_requests_endpoint(
    episode_id: str | None = None,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    return {"items": list_approval_requests(episode_id=episode_id)}


@router.post("/approval-requests/{approval_id}/decide")
def decide_approval_request(
    approval_id: str,
    decision: str,
    justification: str = "",
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    if decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="decision must be 'approved' or 'rejected'")
    req = get_approval_request(approval_id)
    if req is None:
        raise HTTPException(status_code=404, detail="approval request not found")
    if settings.auth_enabled and actor.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin role required to decide approvals")
    now = utcnow()
    with connect() as conn:
        conn.execute(
            "UPDATE zeazverse_approval_requests SET decision=?, decided_by=?, decided_at=?, justification=?, updated_at=? WHERE id=?",
            (decision, actor["username"], now, justification, now, approval_id),
        )
        updated = _row_if_available(conn, approval_id)
    audit(
        "zeazverse.approval_request.decide",
        actor=actor["username"],
        entity_type="approval_request",
        entity_id=approval_id,
        details={"decision": decision, "justification": justification},
    )
    return {"approval_request": updated or req}


def _row_if_available(conn: Any, approval_id: str) -> dict[str, Any] | None:
    from ..zeazverse.store import _row
    return _row(conn, "SELECT * FROM zeazverse_approval_requests WHERE id=?", (approval_id,))


# ---------------------------------------------------------------------------
# Publications (Sec. 12-13; private by default, human approval to publish)
# ---------------------------------------------------------------------------

@router.post("/publications")
def create_publication(
    payload: PublicationRequest, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    episode = get_episode(payload.episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="episode not found")
    if get_publication_by_idempotency_key(payload.idempotency_key or payload.id) is not None:
        raise HTTPException(status_code=409, detail="publication idempotency key already exists")
    pub = payload.model_dump()
    pub["owner"] = actor["username"]
    # Default to private unless explicitly overridden.
    pub.setdefault("privacy", "private")
    result = upsert_publication(pub)
    audit("zeazverse.publication.create", actor=actor["username"], entity_type="publication", entity_id=result["id"])
    return {"publication": result}


@router.get("/publications/{publication_id}")
def get_publication_endpoint(
    publication_id: str, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    pub = get_publication(publication_id)
    if pub is None:
        raise HTTPException(status_code=404, detail="publication not found")
    return {"publication": pub}


@router.get("/publications")
def list_publications_endpoint(
    episode_id: str | None = None,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    return {"items": list_publications(episode_id=episode_id)}


# ---------------------------------------------------------------------------
# Analytics (Sec. 19)
# ---------------------------------------------------------------------------

@router.post("/analytics")
def create_analytics_snapshot(
    payload: AnalyticsSnapshotRequest, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    snapshot = payload.model_dump()
    result = upsert_analytics_snapshot(snapshot)
    audit("zeazverse.analytics.create", actor=actor["username"], entity_type="analytics_snapshot", entity_id=result["id"])
    return {"analytics": result}


@router.get("/analytics")
def list_analytics_endpoint(
    channel_id: str | None = None,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    return {"items": list_analytics_snapshots(channel_id=channel_id)}


# ---------------------------------------------------------------------------
# Workflow runs (Sec. 19 orchestrator)
# ---------------------------------------------------------------------------

@router.post("/workflow-runs")
def create_workflow_run(
    payload: WorkflowRunRequest, actor: dict[str, str] = Depends(current_actor)
) -> dict[str, object]:
    run = payload.model_dump()
    result = upsert_workflow_run(run)
    audit("zeazverse.workflow_run.create", actor=actor["username"], entity_type="workflow_run", entity_id=result["id"])
    return {"workflow_run": result}


@router.get("/workflow-runs")
def list_workflow_runs_endpoint(
    episode_id: str | None = None,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    return {"items": list_workflow_runs(episode_id=episode_id)}


# ---------------------------------------------------------------------------
# Audit events (Sec. 16)
# ---------------------------------------------------------------------------

@router.get("/audit-events")
def list_audit_events_endpoint(
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int = 100,
    actor: dict[str, str] = Depends(current_actor),
) -> dict[str, object]:
    return {"items": list_audit_events(entity_type=entity_type, entity_id=entity_id, limit=limit)}


# ---------------------------------------------------------------------------
# Episode state machine reference (Sec. 13)
# ---------------------------------------------------------------------------

@router.get("/states")
def list_episode_states() -> dict[str, object]:
    return {
        "states": list(EPISODE_STATES),
        "transitions": {k: sorted(v) for k, v in EPISODE_TRANSITIONS.items()},
        "approval_guard_states": sorted(APPROVAL_GUARD_STATES),
    }
