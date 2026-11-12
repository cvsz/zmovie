"""Agent 10 -- Audio Director

Manages original music, dialogue, narration and sound effects for ZEAZVERSE.

Responsibilities:
- Manage original music, dialogue, narration and sound effects
- Implement model-specific adapters for audio generation
- Support Spec #9: Provider selection, model configuration, generation parameters
- Support Spec #10: Audio normalization, voice synchronization checks, sound effects
- Support audio asset hashes and revision history (Spec #4 consistency rules)
- Generate dialogue plans with lip-sync timing

Agent Outputs:
- audio_plan: Audio generation configuration
- mixing_plan: Mixing and balance configuration
- sound_effects: List of sound effects with timestamps
- dialogue_plan: Dialogue script with lip-sync timing
- artifact_manifest: Audio assets with hashes
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class AudioFormat(Enum):
    """Supported audio formats."""
    AAC = auto()  # Advanced Audio Coding (default for YouTube)
    MP3 = auto()
    WAV = auto()
    OGG = auto()


class AudioType(Enum):
    """Types of audio content."""
    MUSIC = auto()  # Background music, theme songs
    DIALOGUE = auto()  # Character dialogue
    NARRATION = auto()  # Voice-over narration
    SOUND_EFFECT = auto()  # SFX (footsteps, impacts, etc.)
    AMBIENT = auto()  # Background ambience, environment sounds


class AudioQuality(Enum):
    """Audio quality levels."""
    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()


@dataclass
class AudioSegment:
    """A segment of audio with timing."""
    segment_id: str
    audio_type: AudioType
    start_time: float  # seconds from scene start
    duration: float  # seconds
    text: str  # dialogue text or narration text
    language: str  # language code (e.g., "en", "th")
    voice_profile: str  # voice model/character
    lip_sync_reference: str | None = None  # reference frame ID
    volume_normalization: float = 1.0  # -1.0 to 1.0
    fade_in: float = 0.0  # seconds
    fade_out: float = 0.0  # seconds


@dataclass
class MixingPlan:
    """Audio mixing configuration."""
    track_id: str
    elements: list[str]  # audio asset IDs being mixed
    volume_levels: dict[str, float]  # per-element volume adjustment
    panning: dict[str, float]  # stereo panning (-1.0 to 1.0)
    equalization: dict[str, dict[str, float]]  # per-element EQ settings
    compression: dict[str, Any]  # compressor settings
    reverb: dict[str, Any]  # reverb settings


@dataclass
class AudioOutput:
    """Complete audio production output."""
    scene_id: str
    character_id: str
    audio_plan: dict[str, Any]
    mixing_plan: MixingPlan
    sound_effects: list[AudioSegment]
    dialogue_plan: list[AudioSegment]
    artifact_manifest: dict[str, str]  # hash -> format mapping


class AudioDirectorAgent:
    """Agent 10 -- Audio Director implementation."""

    AGENT_ID = "AGENT_10"
    AGENT_NAME = "Audio Director"
    DESCRIPTION = "Manages original music, dialogue, narration and sound effects"

    def __init__(self, default_format: AudioFormat = AudioFormat.AAC,
                 default_quality: AudioQuality = AudioQuality.HIGH):
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID
        self.default_format = default_format
        self.default_quality = default_quality

    def plan_audio_for_scene(
        self, scene_id: str, character_id: str,
        dialogue: list[str] | None = None,
        music_theme: str | None = None,
        sfx_requirements: list[str] | None = None,
    ) -> AudioOutput:
        """Plan audio production for a scene."""

        # Generate dialogue segments
        dialogue_segments = self._plan_dialogue(dialogue or [], character_id)

        # Plan sound effects
        sfx_segments = self._plan_sfx(sfx_requirements or [])

        # Plan music
        music_plan = self._plan_music(music_theme or "original_story")

        # Create mixing plan
        mixing_plan = self._create_mixing_plan(dialogue_segments, sfx_segments, music_plan)

        # Generate artifact manifest
        artifact_manifest = self._create_artifact_manifest(
            dialogue_segments, sfx_segments, music_plan
        )

        # Generate dialogue plan (detailed)
        detailed_dialogue = self._generate_detailed_dialogue(dialogue_segments)

        return AudioOutput(
            scene_id=scene_id,
            character_id=character_id,
            audio_plan={
                "format": self.default_format.name,
                "quality": self.default_quality.name,
                "music_theme": music_theme or "original_story",
            },
            mixing_plan=mixing_plan,
            sound_effects=sfx_segments,
            dialogue_plan=detailed_dialogue,
            artifact_manifest=artifact_manifest,
        )

    def _plan_dialogue(
        self, dialogue_texts: list[str], character_id: str
    ) -> list[AudioSegment]:
        """Plan dialogue audio segments."""
        segments = []
        for i, text in enumerate(dialogue_texts):
            segment = AudioSegment(
                segment_id=f"dialog_{character_id}_{uuid4().hex[:4]}_{i}",
                audio_type=AudioType.DIALOGUE,
                start_time=i * 5.0,  # Simplified: 5s per line
                duration=3.0,
                text=text,
                language="en",
                voice_profile=character_id,
                fade_in=0.3,
                fade_out=0.3,
            )
            segments.append(segment)
        return segments

    def _plan_sfx(self, requirements: list[str]) -> list[AudioSegment]:
        """Plan sound effects."""
        sfx_types = {
            "footsteps": "footstep on gravel",
            "impact": "impact hit",
            "magic": "magical sparkle",
            "door": "door creaking",
            "wind": "wind blowing",
            "crowd": "ambient crowd murmur",
        }

        segments = []
        for i, req in enumerate(requirements):
            sfx_type = req.lower()
            description = sfx_types.get(sfx_type, req)

            segment = AudioSegment(
                segment_id=f"sfx_{uuid4().hex[:4]}_{i}",
                audio_type=AudioType.SOUND_EFFECT,
                start_time=round(i * 2.0, 2),
                duration=1.0,
                text=description,
                language="en",
                voice_profile="sfx",
                fade_in=0.1,
                fade_out=0.1,
            )
            segments.append(segment)
        return segments

    def _plan_music(self, theme: str) -> dict[str, Any]:
        """Plan music track."""
        theme_mappings = {
            "dreams": {"mood": "ethereal, ambient", "instrument": "synth pads"},
            "cinematic_action": {"mood": "dramatic, orchestral", "instrument": "full orchestra"},
            "fantasy_adventures": {"mood": "magical, epic", "instrument": "choir + strings"},
            "cyberpunk_stories": {"mood": "noir, synth-wave", "instrument": "synthesizer"},
            "martial_arts": {"mood": "intense, rhythmic", "instrument": "percussion + strings"},
            "comedy_shorts": {"mood": "light, playful", "instrument": "piano + pizzicato"},
            "sci_fi_exploration": {"mood": "futuristic, clean", "instrument": "synth + electronic"},
            "original_story": {"mood": "balanced, cinematic", "instrument": "light orchestral"},
        }

        theme_config = theme_mappings.get(theme, theme_mappings["original_story"])
        return {
            "mood": theme_config["mood"],
            "instrument": theme_config["instrument"],
            "duration_estimate": 30.0,
            "volume_level": 0.3,
        }

    def _create_mixing_plan(
        self, dialogue: list[AudioSegment],
        sfx: list[AudioSegment],
        music: dict[str, Any],
    ) -> MixingPlan:
        """Create audio mixing configuration."""
        elements = []
        volume_levels = {}
        panning = {}
        equalization = {}

        # Dialogue elements
        for i, seg in enumerate(dialogue):
            elements.append(f"dialog_{i}")
            volume_levels[f"dialog_{i}"] = 0.8
            panning[f"dialog_{i}"] = 0.0  # Center
            equalization[f"dialog_{i}"] = {
                "low_cut": 80.0,
                "presence": 2.0,
                "de_ess": 3.0,
            }

        # Sound effects
        for i, seg in enumerate(sfx):
            elements.append(f"sfx_{i}")
            volume_levels[f"sfx_{i}"] = 0.5
            panning[f"sfx_{i}"] = 0.5  # Slight right
            equalization[f"sfx_{i}"] = {
                "low_cut": 60.0,
                "brightness": 1.5,
            }

        # Music
        elements.append("music")
        volume_levels["music"] = music["volume_level"]
        panning["music"] = 0.0
        equalization["music"] = {
            "low_cut": 40.0,
            "warmth": 1.5,
        }

        return MixingPlan(
            track_id=f"track_{uuid4().hex[:8]}",
            elements=elements,
            volume_levels=volume_levels,
            panning=panning,
            equalization=equalization,
            compression={"threshold": -16.0, "ratio": 3.0, "attack": 10, "release": 100},
            reverb={"room_size": 0.3, "decay": 1.5, "mix": 0.25},
        )

    def _create_artifact_manifest(
        self, dialogue: list[AudioSegment],
        sfx: list[AudioSegment],
        music: dict[str, Any],
    ) -> dict[str, str]:
        """Create artifact manifest with hashes."""
        manifest = {}
        import hashlib

        # Generate hashes for each audio segment
        for seg in dialogue:
            hash_input = f"{seg.segment_id}_dialog_{seg.text[:20]}"
            manifest[seg.segment_id] = hashlib.md5(hash_input.encode()).hexdigest()[:16]

        for seg in sfx:
            hash_input = f"{seg.segment_id}_sfx_{seg.text[:20]}"
            manifest[seg.segment_id] = hashlib.md5(hash_input.encode()).hexdigest()[:16]

        # Music hash
        music_hash = hashlib.md5(
            f"music_{music['mood']}_{music['instrument']}".encode()
        ).hexdigest()[:16]
        manifest["music_track"] = music_hash

        return manifest

    def _generate_detailed_dialogue(
        self, segments: list[AudioSegment]
    ) -> list[AudioSegment]:
        """Generate detailed dialogue plan with lip-sync references."""
        # In a full implementation, this would include:
        # - Lip-sync timing per phoneme
        # - Voice actor characteristics
        # - Emotional state markers
        # - Language-specific prosody rules
        # For now, return the segments with additional metadata

        detailed = []
        for seg in segments:
            detailed.append(AudioSegment(
                segment_id=seg.segment_id,
                audio_type=seg.audio_type,
                start_time=seg.start_time,
                duration=seg.duration,
                text=seg.text,
                language=seg.language,
                voice_profile=seg.voice_profile,
                lip_sync_reference=f"ref_frame_{seg.segment_id}",
                volume_normalization=seg.volume_normalization,
                fade_in=seg.fade_in,
                fade_out=seg.fade_out,
            ))
        return detailed

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "default_format": self.default_format.name,
            "default_quality": self.default_quality.name,
            "capability": "audio_direction",
        }


# Module-level agent instance
agent = AudioDirectorAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute an Audio Director agent action.

    Convenience function for running agent actions from API or workflow orchestration.

    Args:
        action: The action to execute (e.g., "plan_audio", "status_check")
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "plan_audio":
        scene_id = kwargs.get("scene_id", "scene_default")
        character_id = kwargs.get("character_id", "lalin")
        dialogue = kwargs.get("dialogue")
        music_theme = kwargs.get("music_theme")
        sfx_requirements = kwargs.get("sfx_requirements")

        output = agent_obj.plan_audio_for_scene(
            scene_id=scene_id,
            character_id=character_id,
            dialogue=dialogue,
            music_theme=music_theme,
            sfx_requirements=sfx_requirements,
        )

        return {
            "agent": agent_obj.AGENT_ID,
            "action": "plan_audio",
            "status": "completed",
            "scene_id": output.scene_id,
            "character_id": output.character_id,
            "audio_plan": output.audio_plan,
            "mixing_plan": {
                "track_id": output.mixing_plan.track_id,
                "elements": output.mixing_plan.elements,
                "volume_levels": output.mixing_plan.volume_levels,
                "panning": output.mixing_plan.panning,
                "equalization": output.mixing_plan.equalization,
                "compression": output.mixing_plan.compression,
                "reverb": output.mixing_plan.reverb,
            },
            "sound_effects": [
                {
                    "segment_id": sfx.segment_id,
                    "audio_type": sfx.audio_type.name,
                    "start_time": sfx.start_time,
                    "duration": sfx.duration,
                    "text": sfx.text,
                    "fade_in": sfx.fade_in,
                    "fade_out": sfx.fade_out,
                }
                for sfx in output.sound_effects
            ],
            "dialogue_plan": [
                {
                    "segment_id": seg.segment_id,
                    "audio_type": seg.audio_type.name,
                    "start_time": seg.start_time,
                    "duration": seg.duration,
                    "text": seg.text,
                    "language": seg.language,
                    "voice_profile": seg.voice_profile,
                    "lip_sync_reference": seg.lip_sync_reference,
                    "volume_normalization": seg.volume_normalization,
                    "fade_in": seg.fade_in,
                    "fade_out": seg.fade_out,
                }
                for seg in output.dialogue_plan
            ],
            "artifact_manifest": output.artifact_manifest,
        }

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "AudioDirectorAgent",
    "AudioFormat",
    "AudioType",
    "AudioQuality",
    "AudioSegment",
    "MixingPlan",
    "AudioOutput",
    "execute_action",
    "agent",
]