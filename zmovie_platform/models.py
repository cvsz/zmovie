from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Existing zMovie v2 domain models (unchanged)
# ---------------------------------------------------------------------------

@dataclass
class CharacterBible:
    id: str
    name: str
    role: str = "lead"
    appearance: str = ""
    hair: str = ""
    wardrobe: str = ""
    personality: str = ""
    fighting_style: str = ""
    continuity_notes: str = ""
    reference_assets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Shot:
    id: str
    scene_id: str
    order_index: int
    duration_seconds: int = 20
    summary: str = ""
    prompt: str = ""
    negative_prompt: str = ""
    provider: str = "generic"
    status: str = "draft"
    continuity_in: str = ""
    continuity_out: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Scene:
    id: str
    project_id: str
    order_index: int
    title: str
    summary: str = ""
    location: str = ""
    time_of_day: str = "night"
    mood: str = "cinematic"
    continuity_notes: str = ""
    shots: list[Shot] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["shots"] = [shot.to_dict() for shot in self.shots]
        return data


@dataclass
class Project:
    id: str
    name: str
    concept: str
    genre: str = "action"
    visual_style: str = "photorealistic cinematic"
    aspect_ratio: str = "16:9"
    target_duration_seconds: int = 60
    owner: str = "local"
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)
    characters: list[CharacterBible] = field(default_factory=list)
    scenes: list[Scene] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "characters": [item.to_dict() for item in self.characters],
            "scenes": [item.to_dict() for item in self.scenes],
        }


@dataclass
class RenderJob:
    id: str
    project_id: str
    shot_id: str
    provider: str
    status: str = "queued"
    output_path: str = ""
    error: str = ""
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# ZEAZVERSE domain models (Sec. 14 entities)
# ---------------------------------------------------------------------------


@dataclass
class Channel:
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
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChannelIntegration:
    id: str
    channel_id: str
    provider: str = "youtube"
    channel_id_external: str = ""
    access_token_encrypted: str = ""
    refresh_token_encrypted: str = ""
    token_expires_at: str = ""
    scopes: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Character:
    """Canon Character Bible (Sec. 4). Versioned; human approval required for
    canonical changes."""
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
    visual_continuity_rules: list[str] = field(default_factory=list)
    reference_assets: list[str] = field(default_factory=list)
    canonical_hash: str = ""
    status: str = "draft"
    owner: str = "local"
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CharacterVersion:
    id: int
    character_id: str
    version: int
    payload_json: dict[str, Any] = field(default_factory=dict)
    change_reason: str = ""
    approved_by: str = ""
    approved_at: str = ""
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CharacterAsset:
    id: str
    character_id: str
    kind: str
    name: str
    path: str
    sha256: str = ""
    width: int = 0
    height: int = 0
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Series:
    id: str
    channel_id: str
    title: str
    concept: str = ""
    genre: str = ""
    status: str = "planning"
    owner: str = "local"
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Episode:
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
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Script:
    id: str
    episode_id: str
    title: str
    content: str = ""
    language: str = "en"
    thai_localization: dict[str, Any] = field(default_factory=dict)
    version: int = 1
    status: str = "draft"
    owner: str = "local"
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Storyboard:
    id: str
    episode_id: str
    title: str
    scenes: list[dict[str, Any]] = field(default_factory=list)
    version: int = 1
    status: str = "draft"
    owner: str = "local"
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ZScene:
    """ZEAZVERSE scene (Sec. 8 scene prompt contract). Distinct from the
    legacy zMovie ``Scene`` which is project-based."""
    id: str
    storyboard_id: str
    episode_id: str
    scene_number: int
    time_start_seconds: int = 0
    time_end_seconds: int = 30
    characters: list[str] = field(default_factory=list)
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
    model_settings: dict[str, Any] = field(default_factory=dict)
    expected_output: str = ""
    qa_checks: list[str] = field(default_factory=list)
    status: str = "draft"
    owner: str = "local"
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GenerationJob:
    id: str
    scene_id: str
    provider: str = ""
    model: str = ""
    status: str = "queued"
    input_hash: str = ""
    output_path: str = ""
    error: str = ""
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GenerationArtifact:
    id: str
    generation_job_id: str
    kind: str
    path: str
    sha256: str = ""
    width: int = 0
    height: int = 0
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QAReport:
    id: str
    episode_id: str
    passed: bool = False
    checks: list[dict[str, Any]] = field(default_factory=list)
    defects: list[dict[str, Any]] = field(default_factory=list)
    reviewer: str = ""
    reviewed_at: str = ""
    notes: str = ""
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ApprovalRequest:
    id: str
    episode_id: str
    requested_by: str = ""
    requested_at: str = field(default_factory=utcnow)
    decided_by: str = ""
    decided_at: str = ""
    decision: str = "pending"
    justification: str = ""
    idempotency_key: str = ""
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Publication:
    id: str
    episode_id: str
    platform: str = "youtube"
    state: str = "IDEA"
    idempotency_key: str = ""
    external_id: str = ""
    external_url: str = ""
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    playlist: str = ""
    privacy: str = "private"
    schedule_at: str = ""
    published_at: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalyticsSnapshot:
    id: str
    channel_id: str
    episode_id: str = ""
    metric_date: str = ""
    views: int = 0
    watch_time_minutes: int = 0
    average_view_duration_seconds: int = 0
    subscribers_gained: int = 0
    engagement: int = 0
    source: dict[str, Any] = field(default_factory=dict)
    recorded_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowRun:
    id: str
    episode_id: str
    status: str = "running"
    current_state: str = "IDEA"
    error: str = ""
    started_at: str = field(default_factory=utcnow)
    completed_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditEvent:
    id: int
    ts: str
    actor: str
    event: str
    entity_type: str
    entity_id: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
