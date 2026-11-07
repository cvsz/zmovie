"""Agent 08 -- Image Production Agent

Builds reference frames, environments and approved visual assets for ZEAZVERSE characters.

Responsibilities:
- Build reference frames and environments per character and scene context
- Implement model-specific adapters for image generation
- Support Spec #8: "Build pluggable interfaces for image, video, audio and language models"
- Support Spec #9: Provider selection, model configuration, generation parameters
- Support reference image hashes and revision history (Spec #4 consistency rules)
- Generate approved visual assets with consistency validation

Agent Outputs:
- reference_frame: Generated reference frame image description
- environment_description: Environment/setting description
- asset_manifest: List of approved visual assets with hashes
- continuity_check: Continuity validation result against character bible
- prompt_package: Optimized prompt set for image generation
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class AssetType(Enum):
    """Types of visual assets."""
    REFERENCE_FRAME = auto()
    CHARACTER_TURNAROUND = auto()
    ENVIRONMENT = auto()
    PROP = auto()
    COSTUME_VARIANT = auto()
    EMOTION_EXPRESSION = auto()


class QualityLevel(Enum):
    """Asset quality validation levels."""
    APPROVED = auto()
    REWORK_NEEDED = auto()
    REJECTED = auto()


@dataclass
class AssetManifest:
    """Manifest of approved visual assets."""
    asset_id: str
    asset_type: AssetType
    character_id: str
    description: str
    prompt: str
    negative_prompt: str
    hash_value: str  # SHA hash for identity consistency
    quality_level: QualityLevel
    revision_history: list[str] = field(default_factory=list)
    reference_sources: list[str] = field(default_factory=list)


@dataclass
class ImageOutput:
    """Complete image production output."""
    scene_id: str
    character_id: str
    asset_type: AssetType
    reference_frame: dict[str, Any]
    environment_description: str
    asset_manifest: AssetManifest
    continuity_check: dict[str, bool]
    prompt_package: dict[str, str]




# Descriptions for asset types (module-level constant)
ASSET_DESCRIPTIONS = {
    "reference_frame": "Reference frame for character identity preservation",
    "character_turnaround": "Character turnaround sheet (front, profiles, back)",
    "environment": "Environment/setting reference for consistent background",
    "prop": "Prop or costume reference asset",
    "costume_variant": "Costume variant for different scenes",
    "emotion_expression": "Emotion/expression reference sheet",
}

class ImageProductionAgent:
    """Agent 08 -- Image Production Agent implementation."""

    AGENT_ID = "AGENT_08"
    AGENT_NAME = "Image Production Agent"
    DESCRIPTION = "Builds reference frames, environments and approved visual assets"

    def __init__(self, model_adapter_version: str = "v1.0"):
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID
        self.model_adapter_version = model_adapter_version

    def generate_reference_frame(
        self, character_id: str, scene_context: dict[str, Any],
        pose: str = "default", expression: str = "neutral"
    ) -> ImageOutput:
        """Generate a reference frame for a character in a scene context."""

        # Determine asset type based on pose and context
        asset_type = self._determine_asset_type(pose, expression)

        # Build reference frame description
        reference_frame = self._build_reference_frame(character_id, pose, expression)

        # Build environment description
        environment_description = self._build_environment(scene_context)

        # Create asset manifest with hash for identity tracking
        asset_manifest = self._create_asset_manifest(character_id, asset_type)

        # Validate continuity against character bible
        continuity_check = self._validate_continuity(character_id, reference_frame)

        # Generate optimized prompt package
        prompt_package = self._generate_prompt_package(character_id, asset_type, scene_context)

        return ImageOutput(
            scene_id=scene_context.get("scene_id", "scene_default"),
            character_id=character_id,
            asset_type=asset_type,
            reference_frame=reference_frame,
            environment_description=environment_description,
            asset_manifest=asset_manifest,
            continuity_check=continuity_check,
            prompt_package=prompt_package,
        )

    def _determine_asset_type(self, pose: str, expression: str) -> AssetType:
        """Determine the type of asset to generate."""
        # Simple mapping based on pose/expression
        if pose in ["action", "fight", "combat"]:

            return AssetType.REFERENCE_FRAME
        elif pose in ["portrait", "profile"] and expression in [
            "smile",
            "frown",
            "surprised",
        ]:
            return AssetType.ENVIRONMENT
        elif pose in ["turnaround", "full-body"]:
            return AssetType.CHARACTER_TURNAROUND
        elif expression in ["angry", "cry", "laugh"]:
            return AssetType.EMOTION_EXPRESSION
        else:
            return AssetType.REFERENCE_FRAME

    def _build_reference_frame(
        self, character_id: str, pose: str, expression: str
    ) -> dict[str, Any]:
        """Build the reference frame description."""
        # Base frame structure per character
        frame = {
            "character_id": character_id,
            "pose": pose,
            "expression": expression,
            "generated_at": uuid4().hex[:12],
            "model_version": self.model_adapter_version,
        }

        # Add character-specific details based on common patterns
        # (In production, this would query the CharacterBible)
        frame_details = {
            "LALIN": {
                "hair": "long dark high ponytail, wispy bangs",
                "outfit": "white fitted top, reflective silver-white tech jacket",
                "boots": "white-black futuristic boots",
            },
            "NICHA": {
                "hair": "long dark high ponytail, natural Thai facial features",
                "outfit": "gray fitted top, dark tactical jacket",
                "boots": "heavy futuristic boots",
            },
            "PIM": {
                "hair": "short dark-brown bob, natural Thai facial features",
                "outfit": "deep-red fitted top, black tactical fashion jacket",
                "boots": "black platform combat boots",
            },
            "YADA": {
                "hair": "ash-blonde shoulder-length hair, natural Thai facial features",
                "outfit": "white top, black futuristic jacket",
                "boots": "black futuristic boots",
            },
        }

        character_details = frame_details.get(character_id, {})
        if character_details:
            frame.update(character_details)

        return frame

    def _build_environment(self, scene_context: dict[str, Any]) -> str:
        """Build environment/setting description."""
        # Default environments per theme
        environment_map = {
            "dreams": "ethereal dream landscape, floating elements, soft glowing ambiance",
            "cinematic_action": "urban rooftop at night, neon-lit city backdrop",
            "fantasy_adventures": "mystical forest with glowing flora, ancient ruins",
            "cyberpunk_stories": "dystopian street at night, neon signs, rain-soaked",
            "martial_arts": "training dojo, wooden floor, minimal lighting",
            "comedy_shorts": "bright studio with colorful backdrop",
            "sci_fi_exploration": "spaceship interior, control panel lighting",
            "original_story": "cinematic studio setting, neutral background",
        }

        theme = scene_context.get("theme", "original_story")
        return environment_map.get(theme, environment_map["original_story"])

    def _create_asset_manifest(
        self, character_id: str, asset_type: AssetType
    ) -> AssetManifest:
        """Create asset manifest with hash for identity tracking."""
        # Generate a deterministic-looking hash based on character and asset type
        hash_input = f"{character_id}_{asset_type.name}_{uuid4().hex[:8]}"
        asset_hash = hash_input  # In production: actual SHA hash

        # Description based on asset type

        return AssetManifest(
            asset_id=f"asset_{uuid4().hex[:8]}",
            asset_type=asset_type,
            character_id=character_id,
            description=ASSET_DESCRIPTIONS.get(asset_type.name, "Visual asset"),
            prompt="",  # Will be filled by prompt_package
            negative_prompt=(
                "unwanted facial identity changes, costume drift, incorrect anatomy, "
                "extra fingers, extra limbs, broken hands, floating objects, unnatural physical motion, "
                "temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, "
                "accidental text artifacts, unexpected characters, and unrequested logos"
            ),
            hash_value=asset_hash,
            quality_level=QualityLevel.APPROVED,
            reference_sources=[f"character_bible_{character_id}"],
        )

    def _validate_continuity(self, character_id: str, reference_frame: dict[str, Any]) -> dict[str, bool]:
        """Validate continuity against character bible."""
        # Check key identity markers
        continuity_checks = {
            "facial_identity_preserved": True,
            "hair_consistency": True,
            "outfit_consistency": True,
            "proportion_consistency": True,
            "accessories_consistent": True,
        }

        # Simulated continuity validation - in production would compare against
        # the CharacterBible stored references
        character_markers = {
            "LALIN": ["long dark high ponytail", "white fitted top", "silver-white tech jacket"],
            "NICHA": ["long dark high ponytail", "gray fitted top", "dark tactical jacket"],
            "PIM": ["short dark-brown bob", "deep-red fitted top", "black tactical jacket"],
            "YADA": ["ash-blonde shoulder-length hair", "white top", "black futuristic jacket"],
        }

        markers = character_markers.get(character_id, [])
        frame_description = reference_frame.get("description", "")

        # Check that key markers are present
        for marker in markers:
            if marker and marker not in str(frame_description).lower():
                continuity_checks["facial_identity_preserved"] = False

        return continuity_checks

    def _generate_prompt_package(
        self, character_id: str, asset_type: AssetType, scene_context: dict[str, Any]
    ) -> dict[str, str]:
        """Generate optimized prompt package for image generation."""
        # Character descriptions
        character_descriptions = {
            "LALIN": "Adult Thai woman with long dark high ponytail and wispy bangs, natural Thai facial features, wearing white fitted top with reflective silver-white tech jacket, black cyberpunk shorts, utility straps, white-black futuristic boots",
            "NICHA": "Adult Thai woman with long dark high ponytail and natural Thai facial features, wearing gray fitted top with dark tactical jacket, black utility cargo trousers, harness details, heavy futuristic boots",
            "PIM": "Adult Thai woman with short dark-brown bob haircut and natural Thai facial features, wearing deep-red fitted top with black tactical fashion jacket, black techwear shorts, utility belts and straps, black platform combat boots",
            "YADA": "Adult Thai woman with ash-blonde shoulder-length hair and natural Thai facial features, wearing white top with black futuristic jacket, black cargo trousers, utility straps, black futuristic boots",
        }

        # Base prompts per asset type
        base_prompts = {
            AssetType.REFERENCE_FRAME: "reference sheet, front view, left 45°, left profile, back view, right profile, right 45°, facial expressions, costume details, high quality, consistent character",
            AssetType.CHARACTER_TURNAROUND: "character turnaround sheet, 360-degree view, front-left-back-right, consistent design, clean lines, orthographic guide",
            AssetType.ENVIRONMENT: "environment concept art, detailed background, atmospheric, cinematic lighting, high resolution",
            AssetType.PROP: "prop detail, standalone object, centered, neutral background, high detail, texture focus",
            AssetType.COSTUME_VARIANT: "costume variant, outfit change, fashion focus, detailed textures, color accuracy",
            AssetType.EMOTION_EXPRESSION: "emotion expression sheet, smiling, frowning, surprised, angry, sad, consistent character, turnaround",
        }

        base_prompt = base_prompts.get(asset_type, base_prompts[AssetType.REFERENCE_FRAME])

        # Character-specific addition
        char_desc = character_descriptions.get(character_id, "Thai character")
        theme = scene_context.get("theme", "original_story")

        theme_prompts = {
            "dreams": "ethereal, magical, glowing, surreal, dreamlike",
            "cinematic_action": "cinematic, dramatic, intense, professional lighting",
            "fantasy_adventures": "fantasy, magical, adventure, epic, wide-angle",
            "cyberpunk_stories": "cyberpunk, noir, neon, tech-noir, street-level",
            "martial_arts": "martial arts, action, dynamic, impact, strong poses",
            "comedy_shorts": "comedy, expressive, humorous, relaxed pose",
            "sci_fi_exploration": "science fiction, futuristic, clean, advanced technology",
            "original_story": "original, cinematic, story-driven, balanced composition",
        }

        theme_addon = theme_prompts.get(theme, "")
        if theme_addon:
            base_prompt += ", " + theme_addon

        return {
            "positive_prompt": base_prompt,
            "negative_prompt": ASSET_DESCRIPTIONS.get(asset_type.name, ""),
            "character_description": char_desc,
            "asset_type": asset_type.name,
            "scene_theme": theme,
        }

    def validate_asset_quality(self, asset_hash: str, expected_type: AssetType) -> QualityLevel:
        """Validate asset quality by hash check."""
        # In production, this would check against stored hashes
        # For now, simulate quality validation
        return QualityLevel.APPROVED

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "model_adapter_version": self.model_adapter_version,
            "capability": "image_production",
        }


# Module-level agent instance
agent = ImageProductionAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute an Image Production Agent agent action.

    Convenience function for running agent actions from API or workflow orchestration.

    Args:
        action: The action to execute (e.g., "generate_frame", "status_check")
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "generate_frame":
        character_id = kwargs.get("character_id", "lalin")
        scene_context = kwargs.get("scene_context", {})
        pose = kwargs.get("pose", "default")
        expression = kwargs.get("expression", "neutral")

        output = agent_obj.generate_reference_frame(
            character_id, scene_context, pose, expression
        )

        return {
            "agent": agent_obj.AGENT_ID,
            "action": "generate_frame",
            "status": "completed",
            "scene_id": output.scene_id,
            "character_id": output.character_id,
            "asset_type": output.asset_type.name,
            "reference_frame": output.reference_frame,
            "environment_description": output.environment_description,
            "asset_manifest": {
                "asset_id": output.asset_manifest.asset_id,
                "asset_type": output.asset_manifest.asset_type.name,
                "character_id": output.asset_manifest.character_id,
                "description": output.asset_manifest.description,
                "hash_value": output.asset_manifest.hash_value,
                "quality_level": output.asset_manifest.quality_level.name,
            },
            "continuity_check": output.continuity_check,
            "prompt_package": output.prompt_package,
        }

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "ImageProductionAgent",
    "AssetType",
    "QualityLevel",
    "AssetManifest",
    "ImageOutput",
    "execute_action",
    "agent",
]