"""Agent 09 -- Video Production Agent

Coordinates video model adapters, rendering tasks and asset outputs for ZEAZVERSE.

Responsibilities:
- Coordinate video model adapters for different providers
- Manage rendering tasks and asset outputs
- Support Spec #9: Provider selection, model configuration, generation parameters
- Support Spec #10: Video editing pipeline with FFmpeg integration
- Support asynchronous job polling and webhook callbacks when supported
- Support cancellation when supported
- Support retry classification and usage reporting
- Support cost estimation and artifact downloads

Agent Outputs:
- render_job: Rendering job configuration and status
- asset_output: Generated video asset with metadata
- prompt_package: Optimized prompt set for video generation
- editing_plan: FFmpeg-based editing plan
- artifact_manifest: List of generated artifacts with hashes
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4

from zmovie_platform.zeazverse.agents.image_production import (
    AssetManifest,
    AssetType,
    QualityLevel,
)
from zmovie_platform.zeazverse.agents.image_production import (
    execute_action as exec_image,
)


class RenderStatus(Enum):
    """Rendering job status."""
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class VideoFormat(Enum):
    """Supported video formats."""
    MP4 = auto()
    MKV = auto()
    MOV = auto()
    AVI = auto()


class VideoResolution(Enum):
    """Supported video resolutions."""
    RES_1080P = auto()  # 1920x1080
    RES_720P = auto()  # 1280x720
    RES_480P = auto()  # 854x480


@dataclass
class RenderJob:
    """Rendering job configuration."""
    job_id: str
    scene_id: str
    character_id: str
    model_adapter: str
    resolution: VideoResolution
    format: VideoFormat
    duration: float  # seconds
    frame_rate: float  # FPS
    prompt: str
    negative_prompt: str
    status: RenderStatus
    progress: float  # 0.0-1.0
    estimated_cost: float
    artifact_hash: str  # SHA hash of output
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None


@dataclass
class VideoAssetOutput:
    """Generated video asset output."""
    output_id: str
    render_job_id: str
    file_path: str  # Relative path to generated file
    resolution: VideoResolution
    format: VideoFormat
    duration: float
    file_size: float | None  # in bytes
    checksum: str  # MD5 or SHA checksum
    quality_level: QualityLevel
    generated_at: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EditingTask:
    """FFmpeg-based editing task."""
    task_id: str
    input_assets: list[str]  # Asset IDs or file paths
    output_path: str
    operations: list[str]  # e.g., "normalize", "trim", "subtitle"
    parameters: dict[str, Any]  # FFmpeg parameters
    status: RenderStatus
    progress: float  # 0.0-1.0


@dataclass
class VideoProductionOutput:
    """Complete video production output."""
    scene_id: str
    character_id: str
    render_job: RenderJob
    video_asset: VideoAssetOutput | None
    editing_plan: EditingTask | None
    asset_manifest: AssetManifest
    prompt_package: dict[str, str]


class VideoProductionAgent:
    """Agent 09 -- Video Production Agent implementation."""

    AGENT_ID = "AGENT_09"
    AGENT_NAME = "Video Production Agent"
    DESCRIPTION = "Coordinates video model adapters, rendering tasks and asset outputs"

    def __init__(self, default_model: str = "default_adapter",
                 default_resolution: VideoResolution = VideoResolution.RES_1080P,
                 default_format: VideoFormat = VideoFormat.MP4):
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID
        self.default_model = default_model
        self.default_resolution = default_resolution
        self.default_format = default_format

    def create_render_job(
        self, scene_id: str, character_id: str,
        resolution: VideoResolution | None = None,
        format: VideoFormat | None = None,
        duration: float = 30.0,
        frame_rate: float = 30.0,
        prompt: str | None = None,
        negative_prompt: str | None = None,
        model_adapter: str | None = None,
    ) -> RenderJob:
        """Create a new rendering job for a scene."""

        # Use defaults if None provided
        if resolution is None:
            resolution = self.default_resolution
        if format is None:
            format = self.default_format
        if prompt is None:
            prompt = "ZEAZVERSE cinematic shot"
        if negative_prompt is None:
            negative_prompt = (
                "unwanted facial identity changes, costume drift, incorrect anatomy, "
                "extra fingers, extra limbs, broken hands, floating objects, unnatural physical motion, "
                "temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, "
                "accidental text artifacts, unexpected characters, and unrequested logos"
            )
        if model_adapter is None:
            model_adapter = self.default_model

        # Generate deterministic hash based on job parameters
        hash_input = f"{scene_id}_{character_id}_{format.name}_{resolution.name}_{uuid4().hex[:6]}"
        artifact_hash = hash_input  # In production: actual SHA hash

        job = RenderJob(
            job_id=f"job_{uuid4().hex[:8]}",
            scene_id=scene_id,
            character_id=character_id,
            model_adapter=model_adapter,
            resolution=resolution,
            format=format,
            duration=duration,
            frame_rate=frame_rate,
            prompt=prompt,
            negative_prompt=negative_prompt,
            status=RenderStatus.PENDING,
            progress=0.0,
            estimated_cost=0.05,  # Estimated cost per second
            artifact_hash=artifact_hash,
            created_at=uuid4().hex[:12],
        )

        return job

    def update_render_status(self, job_id: str, status: RenderStatus,
                             progress: float | None = None,
                             error_message: str | None = None) -> RenderJob:
        """Update rendering job status (mock implementation)."""
        # In production, this would query the actual job status
        # or interface with the video model adapter
        return RenderJob(
            job_id=job_id,
            scene_id="scene_mock",
            character_id="lalin",
            model_adapter="mock_adapter",
            resolution=VideoResolution.RES_1080P,
            format=VideoFormat.MP4,
            duration=30.0,
            frame_rate=30.0,
            prompt="mock prompt",
            negative_prompt="mock negative",
            status=status,
            progress=progress if progress is not None else 1.0,
            estimated_cost=0.05,
            artifact_hash="mock_hash",
            created_at="mock_created",
            started_at="mock_started",
            completed_at="mock_completed",
            error_message=error_message,
        )

    def generate_video_asset(self, render_job: RenderJob) -> VideoAssetOutput:
        """Generate video asset from a render job (mock implementation)."""
        # In production, this would call the video model adapter
        # and return the actual generated file path and metadata

        output_id = f"output_{uuid4().hex[:8]}"
        file_path = f"generated/{render_job.job_id}_{output_id}.mp4"
        checksum = uuid4().hex[:32]  # SHA-256 hex
        quality = QualityLevel.APPROVED

        # Simulate progress update to COMPLETED
        output = VideoAssetOutput(
            output_id=output_id,
            render_job_id=render_job.job_id,
            file_path=file_path,
            resolution=render_job.resolution,
            format=render_job.format,
            duration=render_job.duration,
            file_size=None,  # Would be actual file size
            checksum=checksum,
            quality_level=quality,
            generated_at=uuid4().hex[:12],
            metadata={
                "model_adapter": render_job.model_adapter,
                "prompt": render_job.prompt[:50] + "..." if len(render_job.prompt) > 50 else render_job.prompt,
                "frame_rate": render_job.frame_rate,
                "resolution": render_job.resolution.name,
            },
        )

        # Update render job status to completed
        render_job.status = RenderStatus.COMPLETED
        render_job.progress = 1.0
        render_job.completed_at = uuid4().hex[:12]

        return output

    def create_editing_plan(
        self, input_assets: list[str],
        operations: list[str] | None = None,
        output_path: str | None = None,
        **ffmpeg_params: Any,
    ) -> EditingTask:
        """Create an FFmpeg-based editing plan."""

        ops = operations or ["normalize"]
        out_path = output_path or f"edited_{uuid4().hex[:8]}.mp4"

        # Default FFmpeg parameters for clip normalization
        default_params = {
            "sample_rate": "44100",
            "audio_codec": "aac",
            "video_codec": "libx264",
            "preset": "medium",
            "crf": "18",
        }
        params = {**default_params, **ffmpeg_params}

        task = EditingTask(
            task_id=f"edit_{uuid4().hex[:8]}",
            input_assets=input_assets,
            output_path=out_path,
            operations=ops,
            parameters=params,
            status=RenderStatus.PENDING,
            progress=0.0,
        )

        return task

    def generate_video_output(
        self, scene_id: str, character_id: str,
        theme: str = "original_story",
        duration: float = 30.0,
        resolution: VideoResolution | None = None,
        format: VideoFormat | None = None,
    ) -> VideoProductionOutput:
        """Generate complete video output for a scene."""

        # Create render job
        render_job = self.create_render_job(
            scene_id=scene_id,
            character_id=character_id,
            resolution=resolution,
            format=format,
            duration=duration,
        )

        # Generate video asset (mock)
        video_asset = self.generate_video_asset(render_job)

        # Create editing plan (basic normalization)
        editing_plan = self.create_editing_plan(
            input_assets=[render_job.job_id],
            operations=["normalize", "validate"],
        )

        # Create asset manifest
        asset_manifest = AssetManifest(
            asset_id=f"asset_{uuid4().hex[:8]}",
            asset_type=AssetType.REFERENCE_FRAME,
            character_id=character_id,
            description="Generated video scene output",
            prompt="",  # Will be filled by prompt_package
            negative_prompt=(
                "unwanted facial identity changes, costume drift, incorrect anatomy, "
                "extra fingers, extra limbs, broken hands, floating objects, unnatural physical motion, "
                "temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, "
                "accidental text artifacts, unexpected characters, and unrequested logos"
            ),
            hash_value=render_job.artifact_hash,
            quality_level=QualityLevel.APPROVED,
            reference_sources=[f"character_bible_{character_id}"],
        )

        # Generate prompt package using image production agent
        image_output = exec_image('generate_frame', character_id=character_id,
                                 scene_context={'theme': theme, 'scene_id': scene_id},
                                 pose='default', expression='neutral')
        prompt_package = image_output.get('prompt_package', {})

        return VideoProductionOutput(
            scene_id=scene_id,
            character_id=character_id,
            render_job=render_job,
            video_asset=video_asset,
            editing_plan=editing_plan,
            asset_manifest=asset_manifest,
            prompt_package=prompt_package,
        )

    def get_job_status(self, job_id: str) -> RenderJob | None:
        """Get rendering job status (mock implementation)."""
        # In production, this would query a job queue or database
        return self.update_render_status(job_id, RenderStatus.PENDING)

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "default_model": self.default_model,
            "default_resolution": self.default_resolution.name,
            "default_format": self.default_format.name,
            "capability": "video_production",
        }


# Module-level agent instance
agent = VideoProductionAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a Video Production Agent agent action.

    Convenience function for running agent actions from API or workflow orchestration.

    Args:
        action: The action to execute (e.g., "create_job", "status_check", "generate_output")
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "create_job":
        scene_id = kwargs.get("scene_id", "scene_default")
        character_id = kwargs.get("character_id", "lalin")
        # Convert string to enum if needed
        resolution_raw = kwargs.get("resolution")
        resolution: VideoResolution
        if isinstance(resolution_raw, str):
            resolution_map = {
                "RES_480P": VideoResolution.RES_480P,
                "RES_720P": VideoResolution.RES_720P,
                "RES_1080P": VideoResolution.RES_1080P,
            }
            resolution = resolution_map.get(resolution_raw.upper(), VideoResolution.RES_1080P)
        elif isinstance(resolution_raw, VideoResolution):
            resolution = resolution_raw
        else:
            resolution = VideoResolution.RES_1080P
        # Convert string to enum if needed
        format_raw = kwargs.get("format")
        format_: VideoFormat
        if isinstance(format_raw, str):
            format_map = {
                "MP4": VideoFormat.MP4,
                "MKV": VideoFormat.MKV,
                "MOV": VideoFormat.MOV,
                "AVI": VideoFormat.AVI,
            }
            format_ = format_map.get(format_raw.upper(), VideoFormat.MP4)
        elif isinstance(format_raw, VideoFormat):
            format_ = format_raw
        else:
            format_ = VideoFormat.MP4
        duration = kwargs.get("duration", 30.0)
        frame_rate = kwargs.get("frame_rate", 30.0)
        prompt = kwargs.get("prompt")
        negative_prompt = kwargs.get("negative_prompt")
        model_adapter = kwargs.get("model_adapter")

        job = agent_obj.create_render_job(
            scene_id=scene_id,
            character_id=character_id,
            resolution=resolution,
            format=format_,
            duration=duration,
            frame_rate=frame_rate,
            prompt=prompt,
            negative_prompt=negative_prompt,
            model_adapter=model_adapter,
        )

        return {
            "agent": agent_obj.AGENT_ID,
            "action": "create_job",
            "status": "completed",
            "job_id": job.job_id,
            "scene_id": job.scene_id,
            "character_id": job.character_id,
            "resolution": job.resolution.name,
            "format": job.format.name,
            "duration": job.duration,
            "frame_rate": job.frame_rate,
            "prompt": job.prompt,
            "render_status": job.status.name,
            "progress": job.progress,
            "estimated_cost": job.estimated_cost,
        }

    elif action == "generate_output":
        scene_id = kwargs.get("scene_id", "scene_default")
        character_id = kwargs.get("character_id", "lalin")
        # Convert string to enum if needed
        resolution_raw = kwargs.get("resolution")
        resolution_val: VideoResolution
        if isinstance(resolution_raw, str):
            resolution_map = {
                "RES_480P": VideoResolution.RES_480P,
                "RES_720P": VideoResolution.RES_720P,
                "RES_1080P": VideoResolution.RES_1080P,
            }
            resolution_val = resolution_map.get(resolution_raw.upper(), VideoResolution.RES_1080P)
        elif isinstance(resolution_raw, VideoResolution):
            resolution_val = resolution_raw
        else:
            resolution_val = VideoResolution.RES_1080P
        # Convert string to enum if needed
        format_raw = kwargs.get("format")
        format_val: VideoFormat
        if isinstance(format_raw, str):
            format_map = {
                "MP4": VideoFormat.MP4,
                "MKV": VideoFormat.MKV,
                "MOV": VideoFormat.MOV,
                "AVI": VideoFormat.AVI,
            }
            format_val = format_map.get(format_raw.upper(), VideoFormat.MP4)
        elif isinstance(format_raw, VideoFormat):
            format_val = format_raw
        else:
            format_val = VideoFormat.MP4
        theme = kwargs.get("theme", "original_story")
        duration = kwargs.get("duration", 30.0)

        output = agent_obj.generate_video_output(
            scene_id=scene_id,
            character_id=character_id,
            theme=theme,
            duration=duration,
            resolution=resolution_val,
            format=format_val,
        )

        return {
            "agent": agent_obj.AGENT_ID,
            "action": "generate_output",
            "status": "completed",
            "scene_id": output.scene_id,
            "character_id": output.character_id,
            "render_job_id": output.render_job.job_id,
            "render_job_status": output.render_job.status.name,
            "render_job_progress": output.render_job.progress,
            "video_asset_id": output.video_asset.output_id if output.video_asset else None,
            "video_asset_path": output.video_asset.file_path if output.video_asset else None,
            "video_asset_format": output.video_asset.format.name if output.video_asset else None,
            "editing_plan_id": output.editing_plan.task_id if output.editing_plan else None,
            "asset_manifest_hash": output.asset_manifest.hash_value,
            "asset_manifest_quality": output.asset_manifest.quality_level.name,
            "prompt_package_positive": output.prompt_package.get("positive_prompt", "")[:60] + "...",
        }

    elif action == "create_editing_plan":
        input_assets = kwargs.get("input_assets", ["asset_1"])
        operations = kwargs.get("operations")
        output_path = kwargs.get("output_path")

        task = agent_obj.create_editing_plan(
            input_assets=input_assets,
            operations=operations,
            output_path=output_path,
        )

        return {
            "agent": agent_obj.AGENT_ID,
            "action": "create_editing_plan",
            "status": "completed",
            "task_id": task.task_id,
            "input_assets": task.input_assets,
            "output_path": task.output_path,
            "operations": task.operations,
            "parameters": task.parameters,
            "status": task.status.name,  # noqa: F601
            "progress": task.progress,
        }

    elif action == "get_status":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "VideoProductionAgent",
    "RenderStatus",
    "VideoFormat",
    "VideoResolution",
    "RenderJob",
    "VideoAssetOutput",
    "EditingTask",
    "VideoProductionOutput",
    "execute_action",
    "agent",
]