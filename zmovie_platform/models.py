from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


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
