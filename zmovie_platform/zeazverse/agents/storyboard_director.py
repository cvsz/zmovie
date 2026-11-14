"""Agent 05 -- Storyboard Director

Transforms scripts into timestamped visual shots with complete scene contracts.

Responsibilities:
- Convert Script Scenes into Storyboard Frames with full specifications
- Implement Story Framework #8: 0-3s hook, 3-8s setting, 8-16s action,
  16-24s climax, 24-30s resolution
- Implement Scene Prompt Contract #9 for each scene:
  Scene identifier, Time range, Characters, Character reference IDs,
  Environment, Subject action, Camera framing, Camera movement,
  Lighting, Physical interaction, Dialogue, Audio,
  Positive prompt, Negative prompt, First-frame continuity,
  Last-frame continuity, Generation model, Model settings,
  Expected output, QA checks
- Implement Global Negative Prompt #9: Unwanted facial identity changes,
  costume drift, incorrect anatomy, extra fingers, extra limbs, broken hands,
  floating objects, unnatural physical motion, temporal flicker, missing
  accessories, inconsistent lighting, distorted backgrounds, accidental text
  artifacts, unexpected characters, and unrequested logos
- Support model-specific adapters rather than assuming every video model
  accepts identical prompt settings

Agent Outputs:
- scene_boards: List of complete scene boards with all contract fields
- prompt_contracts: Validated prompt contracts per scene
- continuity_reports: Character and anatomical continuity checks
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class StoryboardStatus(Enum):
    """Status of a storyboard."""
    IDEA = auto()
    APPROVED = auto()
    RENDERING = auto()
    RENDERED = auto()
    QA_PENDING = auto()
    QA_PASSED = auto()
    BLOCKED = auto()


@dataclass
class SceneBoard:
    """Complete scene board per Scene Prompt Contract #9."""
    scene_id: str
    time_range: str  # "0-3s", "3-8s", "8-16s", "16-24s", "24-30s"
    scene_identifier: str
    characters: list[str]  # character reference IDs
    character_reference_ids: list[str]  # specific reference asset IDs
    environment: str
    subject_action: str
    camera_framing: str
    camera_movement: str
    lighting: str
    physical_interaction: str
    dialogue: str
    audio: str
    positive_prompt: str
    negative_prompt: str
    first_frame_continuity: str
    last_frame_continuity: str
    generation_model: str
    model_settings: dict[str, Any]
    expected_output: str
    qa_checks: list[str]
    status: StoryboardStatus = StoryboardStatus.IDEA


@dataclass
class PromptContract:
    """Validated prompt contract per scene per Spec #9."""
    scene_id: str
    positive_prompt: str
    negative_prompt: str
    expected_output: str
    qa_checks: list[str]
    model_adapter: str
    generation_params: dict[str, Any]

@dataclass
class AgentAction:
    """Standardized agent output format."""
    agent: str
    action: str
    status: str  # "completed", "blocked", "requires_approval"
    data: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

@dataclass
class ContinuityReport:
    """Character and anatomical continuity check result."""
    scene_id: str
    checks: dict[str, bool]  # facial_identity, anatomy, accessories, lighting, etc.
    violations: list[str]
    recommendations: list[str]


class StoryboardDirectorAgent:
    """Agent 05 -- Storyboard Director implementation."""

    AGENT_ID = "AGENT_05"
    AGENT_NAME = "Storyboard Director"
    DESCRIPTION = "Transforms scripts into timestamped visual shots"

    def __init__(self) -> None:
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID

    def create_scene_boards(
        self, script_output: Any, model_adapter: str = "default"
    ) -> list[SceneBoard]:
        """Convert a ScriptOutput into complete SceneBoards per Contract #9.

        Story Framework #8:
        0-3s: Strong visual hook
        3-8s: Introduce setting or conflict
        8-16s: Character action or discovery
        16-24s: Escalation or cinematic climax
        24-30s: Resolution, twist or cliffhanger
        """
        scenes = getattr(script_output, "scenes", [])
        concept = getattr(script_output, "concept", None) or {}
        character_focus = concept.get("character_focus", []) or []

        scene_boards: list[SceneBoard] = []

        for i, scene in enumerate(scenes):
            scene_id = f"scene_{uuid4().hex[:6]}"
            time_range = scene.time_range if scene.time_range else self._story_framework_time(i)

            # Characters from script scene or focus characters
            chars = scene.characters if scene.characters else character_focus[:1] if character_focus else ["lalin"]

            # Character reference IDs (from character bibles)
            ref_ids = self._get_reference_ids(chars)

            # Environment based on theme
            environment = self._env_for_theme(concept.get("theme", ""))

            # Subject action
            subject_action = self._action_for_theme(concept.get("theme", ""))

            # Camera framing
            camera_framing = self._framing_for_theme(concept.get("theme", ""))

            # Camera movement
            camera_movement = self._movement_for_theme(concept.get("theme", ""))

            # Lighting
            lighting = self._lighting_for_theme(concept.get("theme", ""))

            # Physical interaction
            physical_interaction = self._physical_interaction_for_theme(concept.get("theme", ""))

            # Dialogue
            dialogue = scene.dialogue if scene and hasattr(scene, "dialogue") else self._dialogue_for_scene(i, concept)

            # Audio
            audio = self._audio_for_theme(concept.get("theme", ""))

            # Positive prompt
            positive_prompt = self._positive_prompt_contract(concept, scene, i)

            # Negative prompt (Global Negative Prompt #9)
            negative_prompt = self._negative_prompt_contract(concept.get("theme", ""))

            # First-frame continuity
            first_frame_continuity = self._first_continuity(concept, i)

            # Last-frame continuity
            last_frame_continuity = self._last_continuity(concept, i)

            # Generation model
            generation_model = self._generation_model_for_adapter(model_adapter)

            # Model settings
            model_settings = self._model_settings_for_adapter(model_adapter)

            # Expected output
            expected_output = self._expected_output_contract(concept, scene, i)

            # QA checks
            qa_checks = self._qa_checks_contract(concept, scene, i)

            scene_board = SceneBoard(
                scene_id=scene_id,
                time_range=time_range,
                scene_identifier=f"SC_{uuid4().hex[:4]}",
                characters=chars,
                character_reference_ids=ref_ids,
                environment=environment,
                subject_action=subject_action,
                camera_framing=camera_framing,
                camera_movement=camera_movement,
                lighting=lighting,
                physical_interaction=physical_interaction,
                dialogue=dialogue,
                audio=audio,
                positive_prompt=positive_prompt,
                negative_prompt=negative_prompt,
                first_frame_continuity=first_frame_continuity,
                last_frame_continuity=last_frame_continuity,
                generation_model=generation_model,
                model_settings=model_settings,
                expected_output=expected_output,
                qa_checks=qa_checks,
            )

            scene_boards.append(scene_board)

        return scene_boards

    def _story_framework_time(self, idx: int) -> str:
        """Return time range per Story Framework #8."""
        frameworks = ["0-3s", "3-8s", "8-16s", "16-24s", "24-30s"]
        return frameworks[idx] if idx < len(frameworks) else "0-30s"

    def _get_reference_ids(self, chars: list[str]) -> list[str]:
        """Get character reference asset IDs."""
        refs = []
        for c in chars:
            # In full implementation, look up from character bible
            refs.append(f"ref_{uuid4().hex[:8]}")
        return refs

    def _env_for_theme(self, theme: str) -> str:
        environments = {
            "dreams": "psychic landscape",
            "cinematic_action": "urban rooftop",
            "fantasy_adventures": "enchanted forest",
            "cyberpunk_stories": "neo-city alleyway",
            "martial_arts": "training dojo",
            "comedy_shorts": "friendly café",
            "character_relationships": "living room",
            "sci_fi_exploration": "space station corridor",
            "original_story": "various",
        }
        return environments.get(theme, "generic location")

    def _action_for_theme(self, theme: str) -> str:
        actions = {
            "dreams": "exploring surreal imagery",
            "cinematic_action": "engaging in chase",
            "fantasy_adventures": "embarking on quest",
            "cyberpunk_stories": "hacking terminal",
            "martial_arts": "practicing form",
            "comedy_shorts": "misunderstanding situation",
            "character_relationships": "heartfelt conversation",
            "sci_fi_exploration": "investigating anomaly",
            "original_story": "unfolding narrative",
        }
        return actions.get(theme, "developing story")

    def _framing_for_theme(self, theme: str) -> str:
        framings = {
            "dreams": "slow zoom in",
            "cinematic_action": "dynamic tracking",
            "fantasy_adventures": "wide establishing",
            "cyberpunk_stories": "Dutch angle",
            "martial_arts": "medium close-up",
            "comedy_shorts": "loose framing",
            "character_relationships": "two-shot",
            "sci_fi_exploration": "point-of-view",
            "original_story": "standard coverage",
        }
        return framings.get(theme, "standard framing")

    def _movement_for_theme(self, theme: str) -> str:
        movements = {
            "dreams": "slow dolly",
            "cinematic_action": "rapid pan",
            "fantasy_adventures": "steady tracking",
            "cyberpunk_stories": "jerky handheld",
            "martial_arts": "static with cuts",
            "comedy_shorts": "jump cut",
            "character_relationships": "slow push-in",
            "sci_fi_exploration": "gliding",
            "original_story": "match cut",
        }
        return movements.get(theme, "static")

    def _lighting_for_theme(self, theme: str) -> str:
        lightings = {
            "dreams": "soft, diffused",
            "cinematic_action": "high contrast",
            "fantasy_adventures": "golden hour",
            "cyberpunk_stories": "neon, blue wash",
            "martial_arts": "dynamic, directional",
            "comedy_shorts": "even, flat",
            "character_relationships": "warm, intimate",
            "sci_fi_exploration": "cool, sterile",
            "original_story": "three-point",
        }
        return lightings.get(theme, "standard")

    def _physical_interaction_for_theme(self, theme: str) -> str:
        interactions = {
            "dreams": "none (surreal)",
            "cinematic_action": "weapon discharge, fall",
            "fantasy_adventures": "magic spell cast",
            "cyberpunk_stories": "hacking interface",
            "martial_arts": "strike, block",
            "comedy_shorts": "slapstick collision",
            "character_relationships": "embrace, handshake",
            "sci_fi_exploration": "console interaction",
            "original_story": "narrative reveal",
        }
        return interactions.get(theme, "none")

    def _dialogue_for_scene(self, idx: int, concept: dict[str, Any]) -> str:
        themes_dialogue = {
            "dreams": [
                "This feels... familiar yet unknown.",
                "The boundary between sleep and waking blurs.",
            ],
            "cinematic_action": [
                "We need to move, now!",
                "The target is heading for the exit.",
            ],
            "fantasy_adventures": [
                "An ancient power stirs.",
                "The prophecy speaks of our coming.",
            ],
            "cyberpunk_stories": [
                "The firewall's blocking access.",
                "I'm tracing the signal source.",
            ],
            "martial_arts": [
                "Focus your breathing.",
                "The stance is all wrong.",
            ],
            "comedy_shorts": [
                "Wait, you didn't order that?",
                "I thought you said peanuts, not almonds.",
            ],
            "character_relationships": [
                "I never meant for things to escalate this far.",
                "We should have said something sooner.",
            ],
            "sci_fi_exploration": [
                "Readings are off the charts.",
                "This wasn't in the mission parameters.",
            ],
            "original_story": [
                "And so the journey begins.",
                "Nothing will ever be the same.",
            ],
        }
        theme = str(concept.get("theme", ""))
        dialogues = themes_dialogue.get(theme, ["..."])
        return dialogues[idx % len(dialogues)] if dialogues else "..."

    def _audio_for_theme(self, theme: str) -> str:
        audio_plans = {
            "dreams": "ambient soundscape, soft bells",
            "cinematic_action": "orchestral score, driving percussion",
            "fantasy_adventures": "orchestral theme with choir",
            "cyberpunk_stories": "synthesized bass, glitch effects",
            "martial_arts": "traditional drums, rhythmic strikes",
            "comedy_shorts": "pizzicato strings, humorous stabs",
            "character_relationships": "piano, gentle arpeggios",
            "sci_fi_exploration": "synthesized pads, atmospheric",
            "original_story": "full orchestral score",
        }
        return audio_plans.get(theme, "background music")

    def _positive_prompt_contract(self, concept: dict[str, Any], scene: Any, idx: int) -> str:
        theme = concept.get("theme", "") if concept else ""
        # Build positive prompt from theme, content class, character
        content_class = concept.get("content_class", "B") if concept else "B"
        char = concept.get("character_focus", ["lalin"])[0] if concept else "lalin"
        base = f"{theme} style, {content_class.lower()}, {char} central"
        # Add scene-specific elements
        scene_notes = [
            "strong visual hook",
            "character introduction",
            "action sequence",
            "climax resolution",
            "twist ending",
        ]
        return f"{base}, {scene_notes[idx % len(scene_notes)]}"

    def _negative_prompt_contract(self, theme: str) -> str:
        """Global Negative Prompt #9."""
        negative_prompts = {
            "dreams": "unwanted facial identity changes, costume drift, incorrect anatomy, extra fingers, extra limbs, broken hands, floating objects, unnatural physical motion, temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, accidental text artifacts, unexpected characters, and unrequested logos",
            "cinematic_action": "incorrect anatomy, extra fingers, extra limbs, broken hands, floating objects, unnatural physical motion, temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, accidental text artifacts, unexpected characters, and unrequested logos",
            "fantasy_adventures": "broken hands, floating objects, unnatural physical motion, temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, accidental text artifacts, unexpected characters, and unrequested logos",
            "cyberpunk_stories": "unwanted facial identity changes, costume drift, incorrect anatomy, extra fingers, extra limbs, broken hands, floating objects, unnatural physical motion, temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, accidental text artifacts, unexpected characters, and unrequested logos",
            "martial_arts": "incorrect anatomy, extra fingers, extra limbs, broken hands, floating objects, unnatural physical motion, temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, accidental text artifacts, unexpected characters, and unrequested logos",
            "comedy_shorts": "unwanted facial identity changes, costume drift, incorrect anatomy, extra fingers, extra limbs, broken hands, floating objects, unnatural physical motion, temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, accidental text artifacts, unexpected characters, and unrequested logos",
            "character_relationships": "unwanted facial identity changes, costume drift, incorrect anatomy, extra fingers, extra limbs, broken hands, floating objects, unnatural physical motion, temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, accidental text artifacts, unexpected characters, and unrequested logos",
            "sci_fi_exploration": "unwanted facial identity changes, costume drift, incorrect anatomy, extra fingers, extra limbs, broken hands, floating objects, unnatural physical motion, temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, accidental text artifacts, unexpected characters, and unrequested logos",
            "original_story": "unwanted facial identity changes, costume drift, incorrect anatomy, extra fingers, extra limbs, broken hands, floating objects, unnatural physical motion, temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, accidental text artifacts, unexpected characters, and unrequested logos",
        }
        return negative_prompts.get(theme, "unwanted facial identity changes, costume drift, incorrect anatomy, extra fingers, extra limbs, broken hands, floating objects, unnatural physical motion, temporal flicker, missing accessories, inconsistent lighting, distorted backgrounds, accidental text artifacts, unexpected characters, and unrequested logos")

    def _first_continuity(self, concept: dict[str, Any], idx: int) -> str:
        return "maintain character facial features and costume consistency"

    def _last_continuity(self, concept: dict[str, Any], idx: int) -> str:
        return "preserve costume details and lighting continuity"

    def _generation_model_for_adapter(self, adapter: str) -> str:
        models = {"default": "default-model", "lipsum": "lipsum-model", "vision": "vision-model"}
        return models.get(adapter, "default-model")

    def _model_settings_for_adapter(self, adapter: str) -> dict[str, Any]:
        return {
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 2048,
            "presence_penalty": 0.1,
            "frequency_penalty": 0.1,
        }

    def _expected_output_contract(self, concept: dict[str, Any], scene: Any, idx: int) -> str:
        theme = concept.get("theme", "") if concept else ""
        return f"{theme} episode segment {idx + 1}: {self._story_framework_time(idx)} with character consistency and quality standards"

    def _qa_checks_contract(self, concept: dict[str, Any], scene: Any, idx: int) -> list[str]:
        theme = concept.get("theme", "") if concept else ""
        base_checks = [
            "facial_identity_consistency",
            "anatomy_correctness",
            "accessory_presence",
            "lighting_consistency",
            "temporal_flicker_free",
            "background_stability",
            "no_accidental_text",
            "no_unexpected_characters",
            "no_unrequested_logos",
        ]
        # Theme-specific additional checks
        theme_addons = {
            "dreams": ["reality_boundary_check"],
            "cinematic_action": ["action_coherence"],
            "fantasy_adventures": ["magic_logic"],
            "cyberpunk_stories": ["tech_plausibility"],
            "martial_arts": ["physics_plausibility"],
            "comedy_shorts": ["joke_consistency"],
            "character_relationships": ["dialogue_consistency"],
            "sci_fi_exploration": ["science_plausibility"],
            "original_story": ["narrative_coherence"],
        }
        addons = theme_addons.get(theme, [])
        return base_checks + addons

    def get_status(self) -> AgentAction:
        """Return agent status action."""
        return AgentAction(
            agent=self.AGENT_ID,
            action="status_check",
            status="ready",
            data={"agent": self.AGENT_NAME, "capability": "storyboard_generation"},
        )


# Module-level agent instance
agent = StoryboardDirectorAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> AgentAction:
    """Execute a Storyboard Director agent action.

    Convenience function for running agent actions from API or workflow orchestration.

    Args:
        action: The action to execute (e.g., "create_boards", "status_check")
        **kwargs: Arguments specific to the action

    Returns:
        AgentAction with standardized output format
    """
    agent_obj = agent

    if action == "create_boards":
        script_output = kwargs.get("script_output")
        model_adapter = kwargs.get("model_adapter", "default")

        if not script_output:
            return AgentAction(
                agent=agent_obj.AGENT_ID,
                action="create_boards",
                status="blocked",
                error="No script_output provided",
            )

        scene_boards = agent_obj.create_scene_boards(script_output, model_adapter)

        return AgentAction(
            agent=agent_obj.AGENT_ID,
            action="create_boards",
            status="completed",
            data={"scene_boards": [
                {
                    "scene_id": sb.scene_id,
                    "time_range": sb.time_range,
                    "scene_identifier": sb.scene_identifier,
                    "characters": sb.characters,
                    "character_reference_ids": sb.character_reference_ids,
                    "environment": sb.environment,
                    "subject_action": sb.subject_action,
                    "camera_framing": sb.camera_framing,
                    "camera_movement": sb.camera_movement,
                    "lighting": sb.lighting,
                    "physical_interaction": sb.physical_interaction,
                    "dialogue": sb.dialogue,
                    "audio": sb.audio,
                    "positive_prompt": sb.positive_prompt,
                    "negative_prompt": sb.negative_prompt,
                    "first_frame_continuity": sb.first_frame_continuity,
                    "last_frame_continuity": sb.last_frame_continuity,
                    "generation_model": sb.generation_model,
                    "model_settings": sb.model_settings,
                    "expected_output": sb.expected_output,
                    "qa_checks": sb.qa_checks,
                    "status": sb.status.name,
                }
                for sb in scene_boards
            ]},
        )

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return AgentAction(
            agent=agent_obj.AGENT_ID,
            action=action,
            status="blocked",
            error=f"Unknown action: {action}",
        )


# Export for API/workflow usage
__all__ = [
    "StoryboardDirectorAgent",
    "SceneBoard",
    "PromptContract",
    "ContinuityReport",
    "AgentAction",
    "execute_action",
    "agent",
]