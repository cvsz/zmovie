"""Agent 06 -- Cinematographer

Designs camera movement, lighting, framing and composition for each scene.

Responsibilities:
- Define camera movement, lighting, framing and composition per scene
- Implement model-specific adapters rather than assuming every video model
  accepts identical prompt settings
- Support FFmpeg-based video editing pipeline functions:
  - Clip normalization
  - Resolution and frame-rate validation
  - Shot assembly
  - Transition handling
  - Audio normalization
  - Voice synchronization checks
- Support Spec #9: Provider selection, model configuration, generation parameters
- Support Spec #10: Video editing with preserving input asset versions

Agent Outputs:
- camera_movement_spec: Camera movement description and parameters
- lighting_spec: Lighting setup with color temperature and intensity
- framing_spec: Camera framing and composition description
- positive_prompt: Camera-focused positive prompt
- negative_prompt: Camera-focused negative prompt (from Spec #9 Global Negative Prompt)
- transition_spec: Transition handling between shots
- shot_assembly_plan: Shot assembly order and timing
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class CinematographyStyle(Enum):
    """Supported cinematography styles."""
    DREAMY = auto()
    CINEMATIC = auto()
    FANTASY = auto()
    CYBERPUNK = auto()
    MARTIAL_ARTS = auto()
    COMEDY = auto()
    SCI_FI = auto()
    DOCUMENTARY = auto()


@dataclass
class CameraSpec:
    """Camera specification for a scene."""
    camera_id: str
    camera_type: str  # e.g., "steadycam", "handheld", "dolly", "drone"
    framing: str  # e.g., "close-up", "medium-shot", "wide-shot"
    movement: str  # e.g., "pan", "tilt", "dolly-in", "dolly-out"
    duration: float  # seconds
    speed: float  # movement speed
    acceleration: float  # acceleration factor
    stabilization: bool  # whether stabilization is applied
    color_temperature: float  # Kelvin (3200-6500)
    iris: float  # f-stop value
    focal_length: float  # mm
    focus_distance: float  # meters


@dataclass
class LightingSpec:
    """Lighting specification for a scene."""
    key_light: dict[str, Any]  # direction, intensity, color
    fill_light: dict[str, Any]  # direction, intensity, color
    back_light: dict[str, Any]  # direction, intensity, color
    ambient_light: dict[str, Any]  # color, intensity
    color_temperature: float  # Kelvin
    intensity: float  # 0.0-1.0
    shadows: str  # "soft", "hard", "mixed"
    highlights: str  # "balanced", "blown", "controlled"
    contrast: float  # 0.0-1.0


@dataclass
class CinematographyOutput:
    """Complete cinematography output for a scene."""
    scene_id: str
    camera_spec: CameraSpec
    lighting_spec: LightingSpec
    positive_prompt: str
    negative_prompt: str
    transition_in: str  # transition from previous shot
    transition_out: str  # transition to next shot
    shot_assembly_order: int
    retention_metadata: dict[str, Any]


class CinematographerAgent:
    """Agent 06 -- Cinematographer implementation."""

    AGENT_ID = "AGENT_06"
    AGENT_NAME = "Cinematographer"
    DESCRIPTION = "Designs camera movement, lighting, framing and composition"

    def __init__(self, style: CinematographyStyle = CinematographyStyle.CINEMATIC):
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID
        self.style = style

    def design_scene_cinematography(
        self, scene_id: str, theme: str, character_count: int,
        is_action_sequence: bool = False
    ) -> CinematographyOutput:
        """Design complete cinematography for a scene based on theme and action level."""

        # Determine camera style based on theme and action
        camera_style = self._determine_style(theme, is_action_sequence)

        # Create camera specification
        camera_spec = self._design_camera_spec(theme, camera_style, character_count, is_action_sequence)

        # Create lighting specification
        lighting_spec = self._design_lighting_spec(theme, camera_style, is_action_sequence)

        # Generate prompts
        positive_prompt = self._generate_positive_prompt(theme, camera_style, is_action_sequence)
        negative_prompt = self._generate_negative_prompt(theme, is_action_sequence)

        # Determine transitions
        transition_in = self._determine_transition_in(theme, is_action_sequence)
        transition_out = self._determine_transition_out(theme, is_action_sequence)

        return CinematographyOutput(
            scene_id=scene_id,
            camera_spec=camera_spec,
            lighting_spec=lighting_spec,
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            transition_in=transition_in,
            transition_out=transition_out,
            shot_assembly_order=1,  # Will be updated by orchestrator
            retention_metadata={
                "style": self.style.name,
                "theme": theme,
                "generated_at": uuid4().hex[:12],
            },
        )

    def _determine_style(self, theme: str, is_action: bool) -> CinematographyStyle:
        """Determine cinematography style based on theme and action level."""
        style_map = {
            "dreams": CinematographyStyle.DREAMY,
            "cinematic_action": CinematographyStyle.CINEMATIC,
            "fantasy_adventures": CinematographyStyle.FANTASY,
            "cyberpunk_stories": CinematographyStyle.CYBERPUNK,
            "martial_arts": CinematographyStyle.MARTIAL_ARTS,
            "comedy_shorts": CinematographyStyle.COMEDY,
            "character_relationships": CinematographyStyle.DREAMY,
            "sci_fi_exploration": CinematographyStyle.SCI_FI,
            "original_story": CinematographyStyle.CINEMATIC,
        }
        base_style = style_map.get(theme, CinematographyStyle.CINEMATIC)
        if is_action:
            # Upgrade one level for action sequences
            upgrade_map = {
                CinematographyStyle.DREAMY: CinematographyStyle.CINEMATIC,
                CinematographyStyle.CINEMATIC: CinematographyStyle.FANTASY,
                CinematographyStyle.FANTASY: CinematographyStyle.CYBERPUNK,
                CinematographyStyle.CYBERPUNK: CinematographyStyle.MARTIAL_ARTS,
                CinematographyStyle.MARTIAL_ARTS: CinematographyStyle.COMEDY,
                CinematographyStyle.COMEDY: CinematographyStyle.SCI_FI,
                CinematographyStyle.SCI_FI: CinematographyStyle.DREAMY,
                CinematographyStyle.DREAMY: CinematographyStyle.CINEMATIC,
            }
            return upgrade_map.get(base_style, base_style)
        return base_style

    def _design_camera_spec(
        self, theme: str, style: CinematographyStyle, character_count: int,
        is_action: bool
    ) -> CameraSpec:
        """Design camera specification for the scene."""
        # Base parameters per style
        style_params: dict[CinematographyStyle, dict[str, object]] = {
            CinematographyStyle.DREAMY: {
                "camera_type": "steadycam",
                "framing": "soft-focus close-up",
                "movement": "slow dolly",
                "speed": 0.3,
                "acceleration": 0.1,
                "color_temp": 4500,
                "iris": 2.8,
                "focal_length": 50,
                "focus_distance": 5,
            },
            CinematographyStyle.CINEMATIC: {
                "camera_type": "dolly",
                "framing": "cinematic medium-shot",
                "movement": "tracking",
                "speed": 0.5,
                "acceleration": 0.2,
                "color_temp": 5600,
                "iris": 4.0,
                "focal_length": 35,
                "focus_distance": 10,
            },
            CinematographyStyle.FANTASY: {
                "camera_type": "steadycam",
                "framing": "wide establishing",
                "movement": "steady tracking",
                "speed": 0.4,
                "acceleration": 0.15,
                "color_temp": 4000,
                "iris": 2.0,
                "focal_length": 24,
                "focus_distance": 8,
            },
            CinematographyStyle.CYBERPUNK: {
                "camera_type": "handheld",
                "framing": "Dutch angle close-up",
                "movement": "jerky handheld",
                "speed": 0.7,
                "acceleration": 0.3,
                "color_temp": 5000,
                "iris": 2.0,
                "focal_length": 35,
                "focus_distance": 3,
            },
            CinematographyStyle.MARTIAL_ARTS: {
                "camera_type": "steadycam",
                "framing": "medium close-up",
                "movement": "dynamic cuts",
                "speed": 0.8,
                "acceleration": 0.5,
                "color_temp": 6000,
                "iris": 3.5,
                "focal_length": 85,
                "focus_distance": 3,
            },
            CinematographyStyle.COMEDY: {
                "camera_type": "handheld",
                "framing": "loose framing",
                "movement": "jump cut",
                "speed": 0.9,
                "acceleration": 0.8,
                "color_temp": 5500,
                "iris": 2.8,
                "focal_length": 35,
                "focus_distance": 5,
            },
            CinematographyStyle.SCI_FI: {
                "camera_type": "dolly",
                "framing": "point-of-view",
                "movement": "gliding",
                "speed": 0.6,
                "acceleration": 0.25,
                "color_temp": 6500,
                "iris": 4.0,
                "focal_length": 24,
                "focus_distance": 15,
            },
        }

        base = style_params.get(style, style_params[CinematographyStyle.CINEMATIC])

        # Extract and cast values
        def _as_float(val: object) -> float:
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                try:
                    return float(val)
                except ValueError:
                    return 0.0
            return 0.0

        def _as_str(val: object) -> str:
            return str(val) if val is not None else ""

        camera_type = _as_str(base.get("camera_type"))
        framing = _as_str(base.get("framing"))
        movement = _as_str(base.get("movement"))
        speed = _as_float(base.get("speed"))
        acceleration = _as_float(base.get("acceleration"))
        color_temp = _as_float(base.get("color_temp"))
        iris = _as_float(base.get("iris"))
        focal_length = _as_float(base.get("focal_length"))
        focus_distance = _as_float(base.get("focus_distance"))

        # Adjust for action sequences
        if is_action:
            speed = min(speed * 1.5, 1.0)
            acceleration = min(acceleration * 1.5, 1.0)
            if camera_type == "steadycam":
                camera_type = "steadycam with motion blur"

        # Adjust for character count
        if character_count > 2:
            framing = "group-shot"
            focal_length = focal_length * 0.7

        return CameraSpec(
            camera_id=f"cam_{uuid4().hex[:8]}",
            camera_type=camera_type,
            framing=framing,
            movement=movement,
            duration=30.0,  # default per spec
            speed=speed,
            acceleration=acceleration,
            stabilization=True,
            color_temperature=color_temp,
            iris=iris,
            focal_length=focal_length,
            focus_distance=focus_distance,
        )

    def _design_lighting_spec(self, theme: str, style: CinematographyStyle,
                              is_action: bool) -> LightingSpec:
        """Design lighting specification for the scene."""
        # Base lighting per style
        style_lighting: dict[CinematographyStyle, dict[str, object]] = {
            CinematographyStyle.DREAMY: {
                "key": {"direction": "45-degree", "intensity": 0.3, "color": "warm-white"},
                "fill": {"direction": "opposite-key", "intensity": 0.5, "color": "soft-white"},
                "back": {"direction": "rear-45", "intensity": 0.2, "color": "warm-white"},
                "ambient": {"color": "warm-white", "intensity": 0.2},
                "temp": 4500,
                "intensity": 0.4,
                "shadows": "soft",
                "highlights": "balanced",
                "contrast": 0.4,
            },
            CinematographyStyle.CINEMATIC: {
                "key": {"direction": "45-degree", "intensity": 0.6, "color": "white"},
                "fill": {"direction": "opposite-key", "intensity": 0.4, "color": "white"},
                "back": {"direction": "rear-45", "intensity": 0.3, "color": "white"},
                "ambient": {"color": "white", "intensity": 0.1},
                "temp": 5600,
                "intensity": 0.7,
                "shadows": "mixed",
                "highlights": "controlled",
                "contrast": 0.6,
            },
            CinematographyStyle.MARTIAL_ARTS: {
                "key": {"direction": "side-45", "intensity": 0.8, "color": "cool-white"},
                "fill": {"direction": "front", "intensity": 0.3, "color": "neutral"},
                "back": {"direction": "rear", "intensity": 0.2, "color": "neutral"},
                "ambient": {"color": "neutral", "intensity": 0.1},
                "temp": 6000,
                "intensity": 0.8,
                "shadows": "hard",
                "highlights": "balanced",
                "contrast": 0.7,
            },
        }

        base = style_lighting.get(style, style_lighting[CinematographyStyle.CINEMATIC])

        # Extract and cast values
        def _get_dict(val: object, default: dict[str, object]) -> dict[str, object]:
            return val if isinstance(val, dict) else default

        def _as_float(val: object, default: float) -> float:
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                try:
                    return float(val)
                except ValueError:
                    return default
            return default

        def _as_str(val: object, default: str) -> str:
            return str(val) if val is not None else default

        key = _get_dict(base.get("key"), {})
        fill = _get_dict(base.get("fill"), {})
        back = _get_dict(base.get("back"), {})
        ambient = _get_dict(base.get("ambient"), {})

        # Adjust for action sequences
        if is_action:
            key_intensity = _as_float(key.get("intensity"), 0.6)
            key["intensity"] = min(key_intensity * 1.3, 1.0)
            base["shadows"] = "hard"
            contrast = _as_float(base.get("contrast"), 0.6)
            base["contrast"] = min(contrast * 1.2, 1.0)

        return LightingSpec(
            key_light=key,
            fill_light=fill,
            back_light=back,
            ambient_light=ambient,
            color_temperature=_as_float(base.get("temp"), 5600.0),
            intensity=_as_float(base.get("intensity"), 0.7),
            shadows=_as_str(base.get("shadows"), "mixed"),
            highlights=_as_str(base.get("highlights"), "controlled"),
            contrast=_as_float(base.get("contrast"), 0.6),
        )

    def _generate_positive_prompt(self, theme: str, style: CinematographyStyle,
                                  is_action: bool) -> str:
        """Generate camera-focused positive prompt."""
        base_prompts = {
            CinematographyStyle.DREAMY: "dreamy cinematography, soft lighting, gentle camera movement, ethereal atmosphere",
            CinematographyStyle.CINEMATIC: "cinematic lighting, 35mm film look, professional composition, dramatic shadows",
            CinematographyStyle.FANTASY: "fantasy cinematography, magical lighting, ethereal glow, wide-angle wonder",
            CinematographyStyle.CYBERPUNK: "cyberpunk noir lighting, neon contrast, Dutch angles, tech-noir atmosphere",
            CinematographyStyle.MARTIAL_ARTS: "martial arts cinematography, dynamic choreography, impact lighting, high contrast",
            CinematographyStyle.COMEDY: "comic timing lighting, even illumination, sitcom-style, soft shadows",
            CinematographyStyle.SCI_FI: "science fiction cinematography, cool-toned lighting, futuristic atmosphere, clean lines",
        }
        base = base_prompts.get(style, base_prompts[CinematographyStyle.CINEMATIC])

        # Add action-specific elements
        if is_action:
            base += ", dynamic camera movement, impact frames, chase sequences"

        # Add theme-specific elements
        theme_prompts = {
            "dreams": "surreal imagery, floating elements",
            "cinematic_action": "dramatic storytelling, narrative flow",
            "fantasy_adventures": "magical atmosphere, quest visualization",
            "cyberpunk_stories": "tech-noir aesthetic, street-level perspective",
            "martial_arts": "impact frames, form emphasis",
            "comedy_shorts": "comic timing, expressive angles",
            "sci_fi_exploration": "future technology visualization",
            "original_story": "cinematic narrative, story-driven",
        }
        theme_addon = theme_prompts.get(theme, "")
        if theme_addon:
            base += ", " + theme_addon

        return base

    def _generate_negative_prompt(self, theme: str, is_action: bool) -> str:
        """Generate camera-focused negative prompt (from Spec #9)."""
        base_negative = "unwanted facial identity changes, costume drift, incorrect anatomy, extra fingers, extra limbs, broken hands, floating objects, unnatural physical motion, temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, accidental text artifacts, unexpected characters, and unrequested logos"

        if is_action:
            base_negative += ", jittery camera movement, shaky footage, lost focus, obscured subjects"

        # Theme-specific additions
        theme_negatives = {
            "dreams": "logical consistency, grounded physics",
            "cinematic_action": "shaky cam, lost continuity",
            "fantasy_adventures": "grounded physics, logical plot holes",
            "cyberpunk_stories": "clean cinematography, no neon overload",
            "martial_arts": "blurred action, lost form",
            "comedy_shorts": "overly serious lighting, dark shadows",
            "sci_fi_exploration": "stagnant camera, no movement",
            "original_story": "static framing, no visual interest",
        }
        theme_addon = theme_negatives.get(theme, "")
        if theme_addon:
            base_negative += ", " + theme_addon

        return base_negative

    def _determine_transition_in(self, theme: str, is_action: bool) -> str:
        """Determine transition from previous shot."""
        transitions = {
            "dreams": "cross-fade",
            "cinematic_action": "hard cut",
            "fantasy_adventures": "match-cut",
            "cyberpunk_stories": "quick cut",
            "martial_arts": "hard cut",
            "comedy_shorts": "wipe",
            "sci_fi_exploration": "dissolve",
            "original_story": "cross-fade",
        }
        return transitions.get(theme, "cross-fade")

    def _determine_transition_out(self, theme: str, is_action: bool) -> str:
        """Determine transition to next shot."""
        transitions = {
            "dreams": "dissolve",
            "cinematic_action": "hard cut",
            "fantasy_adventures": "cross-fade",
            "cyberpunk_stories": "quick cut",
            "martial_arts": "hard cut",
            "comedy_shorts": "wipe",
            "sci_fi_exploration": "dissolve",
            "original_story": "hard cut",
        }
        return transitions.get(theme, "hard cut")

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "style": self.style.name,
            "capability": "cinematography_design",
        }


# Module-level agent instance
agent = CinematographerAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a Cinematographer agent action.

    Convenience function for running agent actions from API or workflow orchestration.

    Args:
        action: The action to execute (e.g., "design_scene", "status_check")
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "design_scene":
        scene_id = kwargs.get("scene_id", "scene_default")
        theme = kwargs.get("theme", "original_story")
        character_count = kwargs.get("character_count", 1)
        is_action = kwargs.get("is_action_sequence", False)

        output = agent_obj.design_scene_cinematography(
            scene_id=scene_id,
            theme=theme,
            character_count=character_count,
            is_action_sequence=is_action,
        )

        return {
            "agent": agent_obj.AGENT_ID,
            "action": "design_scene",
            "status": "completed",
            "scene_id": output.scene_id,
            "camera_spec": {
                "camera_id": output.camera_spec.camera_id,
                "camera_type": output.camera_spec.camera_type,
                "framing": output.camera_spec.framing,
                "movement": output.camera_spec.movement,
                "duration": output.camera_spec.duration,
                "speed": output.camera_spec.speed,
                "acceleration": output.camera_spec.acceleration,
                "stabilization": output.camera_spec.stabilization,
                "color_temperature": output.camera_spec.color_temperature,
                "iris": output.camera_spec.iris,
                "focal_length": output.camera_spec.focal_length,
                "focus_distance": output.camera_spec.focus_distance,
            },
            "lighting_spec": {
                "key_light": output.lighting_spec.key_light,
                "fill_light": output.lighting_spec.fill_light,
                "back_light": output.lighting_spec.back_light,
                "ambient_light": output.lighting_spec.ambient_light,
                "color_temperature": output.lighting_spec.color_temperature,
                "intensity": output.lighting_spec.intensity,
                "shadows": output.lighting_spec.shadows,
                "highlights": output.lighting_spec.highlights,
                "contrast": output.lighting_spec.contrast,
            },
            "positive_prompt": output.positive_prompt,
            "negative_prompt": output.negative_prompt,
            "transition_in": output.transition_in,
            "transition_out": output.transition_out,
            "shot_assembly_order": output.shot_assembly_order,
        }

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "CinematographerAgent",
    "CameraSpec",
    "LightingSpec",
    "CinematographyOutput",
    "execute_action",
    "agent",
]