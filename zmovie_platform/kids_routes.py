"""FastAPI REST routes for Kids Content Factory in zMovie."""

from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .kids_factory import (
    KidsValidationError,
    build_captions_export,
    build_language_variant,
    build_storyboard,
    derive_shorts,
    estimate_cost,
    export_episode_bundle,
    import_episode_bundle,
    kids_safety_check,
    mock_youtube_upload,
    prepare_youtube_metadata,
    resolve_provider_route,
    run_episode_pipeline,
    storyboard_to_timeline,
    suggest_marketing,
    synth_preview_wav,
    timeline_checksum,
    validate_brand,
    validate_channel,
    validate_character,
    validate_episode,
    validate_media_upload,
    validate_music_track,
    validate_provider_route,
    validate_scene,
    validate_schedule_slot,
    validate_script,
    validate_timeline,
    validate_voice_profile,
)

router = APIRouter(prefix="/api/v2/kids", tags=["kids-factory"])


class BrandPayload(BaseModel):
    slug: str
    name: str
    language: str = "en"
    age_band: str = "preschool"
    visual_palette: list[str] = Field(default_factory=list)


class ChannelPayload(BaseModel):
    name: str
    platform: str = "youtube"
    external_account_ref: str = ""
    publishing_settings: dict[str, Any] = Field(default_factory=dict)


class CharacterPayload(BaseModel):
    name: str
    role: str = "guide"
    species: str = "human"
    personality: list[str] = Field(default_factory=list)
    voice_profile: dict[str, Any] = Field(default_factory=dict)
    palette: list[str] = Field(default_factory=list)
    description: str = ""
    negative_prompt: str = ""


class EpisodePayload(BaseModel):
    title: str
    target_age: str = "preschool"
    content_type: str = "counting_song"
    duration_sec: int = 30


class ScriptPayload(BaseModel):
    content_type: str = "nursery_rhyme"
    body: dict[str, Any] = Field(default_factory=dict)


class ScenePayload(BaseModel):
    ordering: int = 1
    duration_seconds: float = 5.0
    visual_prompt: str
    objective: str = ""
    negative_prompt: str = ""


class TimelinePayload(BaseModel):
    tracks: dict[str, Any] = Field(default_factory=dict)


class VoiceProfilePayload(BaseModel):
    name: str
    provider: str = "mock"
    language: str = "en"
    speed: float = 1.0
    style: str = "cheerful"
    voice_id: str = ""
    rights: dict[str, Any] = Field(default_factory=dict)


class MusicTrackPayload(BaseModel):
    title: str
    license: str
    provider: str = "mock"
    duration_seconds: float = 0.0


class ProviderRoutePayload(BaseModel):
    capability: str
    providers: list[str]


class ScheduleSlotPayload(BaseModel):
    slot_at: str
    timezone_name: str = "UTC"


class MediaUploadPayload(BaseModel):
    filename: str
    content_type: str
    size_bytes: int
    max_bytes: int = 25 * 1024 * 1024


class LanguageVariantPayload(BaseModel):
    parent: dict[str, Any]
    language: str


class MarketingPayload(BaseModel):
    episode: dict[str, Any]
    brand_name: str = ""


class VoicePreviewPayload(BaseModel):
    text: str
    speed: float = 1.0
    sample_rate: int = 16000


class SafetyCheckPayload(BaseModel):
    age_band: str = "preschool"
    text: str


class StoryboardGeneratePayload(BaseModel):
    title: str = "Episode Storyboard"
    beats: list[dict[str, Any]] = Field(default_factory=list)
    num_scenes: int = 4


class CaptionsPayload(BaseModel):
    scenes: list[dict[str, Any]]
    format: str = "srt"


class YouTubePublishPayload(BaseModel):
    title: str
    description: str = ""
    idempotency_key: str
    sha256: str = "mock-sha256"


@router.post("/brands/validate")
def validate_brand_endpoint(payload: BrandPayload) -> dict[str, Any]:
    try:
        return {"ok": True, "brand": validate_brand(payload.model_dump())}
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/channels/validate")
def validate_channel_endpoint(payload: ChannelPayload) -> dict[str, Any]:
    try:
        return {"ok": True, "channel": validate_channel(payload.model_dump())}
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/characters/validate")
def validate_character_endpoint(payload: CharacterPayload) -> dict[str, Any]:
    try:
        return {"ok": True, "character": validate_character(payload.model_dump())}
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/episodes/validate")
def validate_episode_endpoint(payload: EpisodePayload) -> dict[str, Any]:
    try:
        return {"ok": True, "episode": validate_episode(payload.model_dump())}
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/scripts/validate")
def validate_script_endpoint(payload: ScriptPayload) -> dict[str, Any]:
    try:
        return {"ok": True, "script": validate_script(payload.model_dump())}
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/scenes/validate")
def validate_scene_endpoint(payload: ScenePayload) -> dict[str, Any]:
    try:
        return {"ok": True, "scene": validate_scene(payload.model_dump())}
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/timelines/validate")
def validate_timeline_endpoint(payload: TimelinePayload) -> dict[str, Any]:
    try:
        validated = validate_timeline(payload.model_dump())
        checksum = timeline_checksum(validated["tracks"])
        return {"ok": True, "timeline": validated, "checksum": checksum}
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/voices/validate")
def validate_voice_endpoint(payload: VoiceProfilePayload) -> dict[str, Any]:
    try:
        return {"ok": True, "voice": validate_voice_profile(payload.model_dump())}
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/voices/preview")
def preview_voice_endpoint(payload: VoicePreviewPayload) -> dict[str, Any]:
    try:
        wav_bytes = synth_preview_wav(
            text=payload.text,
            speed=payload.speed,
            sample_rate=payload.sample_rate,
        )
        return {
            "ok": True,
            "format": "audio/wav",
            "size_bytes": len(wav_bytes),
            "base64": base64.b64encode(wav_bytes).decode("ascii"),
        }
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/music/validate")
def validate_music_endpoint(payload: MusicTrackPayload) -> dict[str, Any]:
    try:
        return {"ok": True, "music": validate_music_track(payload.model_dump())}
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/providers/routes/validate")
def validate_provider_route_endpoint(payload: ProviderRoutePayload) -> dict[str, Any]:
    try:
        validated = validate_provider_route(
            capability=payload.capability,
            providers=payload.providers,
        )
        resolved = resolve_provider_route(
            capability=payload.capability,
            providers=payload.providers,
        )
        return {"ok": True, "route": validated, "resolved": resolved}
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/schedules/slots/validate")
def validate_schedule_slot_endpoint(payload: ScheduleSlotPayload) -> dict[str, Any]:
    try:
        return {
            "ok": True,
            "slot": validate_schedule_slot(
                slot_at=payload.slot_at,
                timezone_name=payload.timezone_name,
            ),
        }
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/media/validate")
def validate_media_endpoint(payload: MediaUploadPayload) -> dict[str, Any]:
    try:
        validate_media_upload(
            filename=payload.filename,
            content_type=payload.content_type,
            size_bytes=payload.size_bytes,
            max_bytes=payload.max_bytes,
        )
        return {"ok": True, "valid": True}
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/variants/draft")
def draft_variant_endpoint(payload: LanguageVariantPayload) -> dict[str, Any]:
    try:
        return {
            "ok": True,
            "variant": build_language_variant(
                parent=payload.parent,
                language=payload.language,
            ),
        }
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/marketing/suggest")
def suggest_marketing_endpoint(payload: MarketingPayload) -> dict[str, Any]:
    try:
        return {
            "ok": True,
            "suggestions": suggest_marketing(
                episode=payload.episode,
                brand_name=payload.brand_name,
            ),
        }
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/safety/check")
def check_safety_endpoint(payload: SafetyCheckPayload) -> dict[str, Any]:
    return kids_safety_check(age_band=payload.age_band, text=payload.text)


@router.post("/storyboard/generate")
def generate_storyboard_endpoint(payload: StoryboardGeneratePayload) -> dict[str, Any]:
    try:
        script_body = {"title": payload.title, "beats": payload.beats}
        scenes = build_storyboard(script_body=script_body, num_scenes=payload.num_scenes)
        timeline = storyboard_to_timeline(scenes, brand_name="Kids Factory")
        return {"ok": True, "scenes": scenes, "timeline": timeline}
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/captions/export")
def export_captions_endpoint(payload: CaptionsPayload) -> dict[str, Any]:
    try:
        return build_captions_export(scenes=payload.scenes, format=payload.format)
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/cost/estimate")
def estimate_cost_endpoint(
    num_scenes: int = Query(4, ge=1, le=100),
    duration_total: float = Query(30.0, ge=1.0, le=3600.0),
    provider: str = Query("mock"),
) -> dict[str, Any]:
    cost = estimate_cost(num_scenes=num_scenes, duration_total=duration_total, provider=provider)
    return {"ok": True, "estimated_credits": cost, "provider": provider}


@router.post("/youtube/mock-upload")
def mock_upload_endpoint(payload: YouTubePublishPayload) -> dict[str, Any]:
    try:
        meta = prepare_youtube_metadata(title=payload.title, description=payload.description)
        result = mock_youtube_upload(
            metadata=meta,
            idempotency_key=payload.idempotency_key,
            sha256=payload.sha256,
        )
        return {"ok": True, "upload": result}
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))



class PipelineRunPayload(BaseModel):
    episode: dict[str, Any]
    budget_credits: float = 0.0
    num_scenes: int = 4


class ShortsDerivePayload(BaseModel):
    parent_episode: dict[str, Any]
    brand_name: str = ""


class BundleExportPayload(BaseModel):
    episode: dict[str, Any]
    brand: dict[str, Any] = Field(default_factory=dict)
    characters: list[dict[str, Any]] = Field(default_factory=list)
    script: dict[str, Any] = Field(default_factory=dict)
    scenes: list[dict[str, Any]] = Field(default_factory=list)
    timeline: dict[str, Any] = Field(default_factory=dict)


class BundleImportPayload(BaseModel):
    bundle: dict[str, Any]
    new_id: str = ""


@router.post("/episodes/pipeline")
def run_pipeline_endpoint(payload: PipelineRunPayload) -> dict[str, Any]:
    try:
        return run_episode_pipeline(
            episode=payload.episode,
            budget_credits=payload.budget_credits,
            num_scenes=payload.num_scenes,
        )
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/episodes/shorts")
def derive_shorts_endpoint(payload: ShortsDerivePayload) -> dict[str, Any]:
    try:
        return {
            "ok": True,
            "short_episode": derive_shorts(
                parent_episode=payload.parent_episode,
                brand_name=payload.brand_name,
            ),
        }
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/episodes/bundle/export")
def export_bundle_endpoint(payload: BundleExportPayload) -> dict[str, Any]:
    try:
        bundle = export_episode_bundle(
            episode=payload.episode,
            brand=payload.brand,
            characters=payload.characters,
            script=payload.script,
            scenes=payload.scenes,
            timeline=payload.timeline,
        )
        return {"ok": True, "bundle": bundle}
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/episodes/bundle/import")
def import_bundle_endpoint(payload: BundleImportPayload) -> dict[str, Any]:
    try:
        return import_episode_bundle(
            bundle=payload.bundle,
            new_id=payload.new_id,
        )
    except KidsValidationError as err:
        raise HTTPException(status_code=400, detail=str(err))
