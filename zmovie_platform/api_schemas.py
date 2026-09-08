from __future__ import annotations

from pydantic import BaseModel, Field


class StoryboardRequest(BaseModel):
    name: str = Field(default="Untitled zMovie", min_length=1, max_length=200)
    concept: str = Field(min_length=3, max_length=20000)
    genre: str = Field(default="action", max_length=80)
    visual_style: str = Field(default="photorealistic premium cinematic realism", max_length=500)
    aspect_ratio: str = Field(default="16:9", max_length=20)
    target_duration_seconds: int = Field(default=60, ge=10, le=3600)
    scene_count: int | None = Field(default=None, ge=1, le=24)


class RenderRequest(BaseModel):
    provider: str = Field(default="mock", max_length=80)
    max_workers: int = Field(default=2, ge=1, le=8)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=1, max_length=500)


class BootstrapRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=10, max_length=500)


class PipelineRequest(StoryboardRequest):
    provider: str = Field(default="mock", max_length=80)


class AssetRequest(BaseModel):
    kind: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    path: str = Field(min_length=1, max_length=2000)


class BilibiliPrepareRequest(BaseModel):
    title: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=10)
    playlist: str = Field(default="", max_length=200)
    content_type: str = Field(default="Original", pattern="^(Original|Repost)$")
    schedule_at: str = Field(default="", max_length=80)


class BilibiliPublishRequest(BaseModel):
    headless: bool = True
