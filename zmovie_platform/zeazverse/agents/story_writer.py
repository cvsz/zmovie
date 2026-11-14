"""Agent 04 -- Story Writer

Generates original scripts, dialogue and episode outlines for ZEAZVERSE.

Responsibilities:
- Create story concepts and episode outlines
- Generate character dialogue and interactions
- Support all content classes: Character Introduction, Cinematic Action,
  Fantasy Adventures, Cyberpunk Stories, Martial Arts, Comedy Shorts,
  Character Relationships, Sci-Fi Exploration, AI Filmmaking Behind the Scenes,
  Original Serialized Episodes
- Each episode: Unique story ID, Series ID, Episode ID, Character references,
  Story concept, Script, Shot list, Storyboard, Asset manifest, Render manifest,
  Audio plan, Editing plan, QA report, Publishing metadata

Agent Outputs:
- story_concept: Story concept with theme and tone
- script: Full script with dialogue and scene descriptions
- episode_outcome: Episode outcome with resolution/twist/cliffhanger
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any
from uuid import uuid4

from zmovie_platform.zeazverse.agents.character_director import (
    AgentAction,
)


class StoryStatus(Enum):
    """Status of a story/episode."""
    IDEA = auto()
    SCRIPT_APPROVED = auto()
    ASSETS_READY = auto()
    RENDERING = auto()
    RENDERED = auto()
    QA_PENDING = auto()
    QA_PASSED = auto()
    READY_FOR_REVIEW = auto()
    APPROVED = auto()
    UPLOADING = auto()
    PRIVATE_UPLOADED = auto()
    PUBLISHED = auto()
    FAILED = auto()
    CANCELLED = auto()
    BLOCKED = auto()


@dataclass
class StoryConcept:
    """Core story concept with theme and tone."""
    story_id: str
    series_id: str
    episode_id: str
    title: str
    theme: str  # e.g., "dreams", "cyber-mission", "rebellion"
    tone: str  # e.g., "dramatic", "comic", "action"
    target_duration: float  # seconds
    target_audience: str  # e.g., "global_english_thai_localized"
    character_focus: list[str]  # character IDs central to this story
    content_class: str  # one of the content factory classes


@dataclass
class ScriptScene:
    """A scene within the script."""
    scene_id: str
    time_range: str  # "0-3s", "3-8s", etc.
    characters: list[str]  # character IDs involved
    environment: str
    subject_action: str
    camera_framing: str
    camera_movement: str
    lighting: str
    dialogue: str
    audio_plan: str
    positive_prompt: str
    negative_prompt: str
    first_frame_continuity: str
    last_frame_continuity: str
    generation_model: str
    model_settings: dict[str, Any]


@dataclass
class ScriptOutput:
    """Complete script output for an episode."""
    story_id: str
    episode_id: str
    concept: StoryConcept
    scenes: list[ScriptScene]
    dialogue_summary: str
    estimated_duration: float
    publishing_metadata: dict[str, Any]


class StoryWriterAgent:
    """Agent 04 -- Story Writer implementation."""

    AGENT_ID = "AGENT_04"
    AGENT_NAME = "Story Writer"
    DESCRIPTION = "Generates original scripts, dialogue and episode outlines"

    def __init__(self) -> None:
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID

    def generate_story_concept(
        self,
        series_id: str,
        episode_id: str,
        content_class: str,
        character_ids: list[str],
        theme_hint: str = "",
    ) -> StoryConcept:
        """Generate a story concept for an episode.

        Supports all content classes from ZEAZVERSE Spec #7:
        A. Character Introduction, B. Cinematic Action, C. Fantasy Adventures,
        D. Cyberpunk Stories, E. Martial Arts, F. Comedy Shorts,
        G. Character Relationships, H. Sci-Fi Exploration,
        I. AI Filmmaking Behind the Scenes, J. Original Serialized Episodes
        """
        # Map content class to theme/tone
        content_class_map = {
            "A": {"theme": "Character Introduction", "tone": "reflective"},
            "B": {"theme": "Cinematic Action", "tone": "dramatic"},
            "C": {"theme": "Fantasy Adventures", "tone": "wondrous"},
            "D": {"theme": "Cyberpunk Stories", "tone": "noir"},
            "E": {"theme": "Martial Arts", "tone": "energetic"},
            "F": {"theme": "Comedy Shorts", "tone": "humorous"},
            "G": {"theme": "Character Relationships", "tone": "emotional"},
            "H": {"theme": "Sci-Fi Exploration", "tone": "curious"},
            "I": {"theme": "AI Filmmaking Behind the Scenes", "tone": "analytical"},
            "J": {"theme": "Original Serialized Episodes", "tone": "epic"},
        }

        mapped = content_class_map.get(content_class, {"theme": "Original Story", "tone": "balanced"})
        if theme_hint:
            mapped["theme"] = theme_hint

        # Determine focusing character(s)
        focus_char = character_ids[0] if character_ids else "lalin"

        story_id = f"story_{uuid4().hex[:8]}"
        episode_id = f"ep_{uuid4().hex[:8]}"

        return StoryConcept(
            story_id=story_id,
            series_id=series_id,
            episode_id=episode_id,
            title=f"{focus_char}_{mapped['theme'].replace(' ', '_')}",
            theme=mapped["theme"],
            tone=mapped["tone"],
            target_duration=30.0,  # default 30 seconds per spec
            target_audience="Global English-speaking viewers with Thai localization",
            character_focus=character_ids,
            content_class=content_class,
        )

    def generate_script(
        self, concept: StoryConcept, scene_count: int = 5
    ) -> ScriptOutput:
        """Generate a complete script for the episode concept.

        Story Framework (Spec #8):
        0-3s: Strong visual hook
        3-8s: Introduce setting or conflict
        8-16s: Character action or discovery
        16-24s: Escalation or cinematic climax
        24-30s: Resolution, twist or cliffhanger
        """
        scenes: list[ScriptScene] = []

        # Generate scenes per story framework
        scene_configs = [
            {"range": "0-3s", "hook": True},
            {"range": "3-8s", "setting": True},
            {"range": "8-16s", "action": True},
            {"range": "16-24s", "climax": True},
            {"range": "24-30s", "resolution": True},
        ]

        for i, sc in enumerate(scene_configs[:scene_count]):
            scene_id = f"scene_{uuid4().hex[:4]}"
            time_range = str(sc["range"])

            # Determine focus based on story theme
            focus_char = concept.character_focus[0] if concept.character_focus else "lalin"

            scenes.append(
                ScriptScene(
                    scene_id=scene_id,
                    time_range=time_range,
                    characters=[focus_char],
                    environment=self._env_for_theme(concept.theme),
                    subject_action=self._action_for_theme(concept.theme),
                    camera_framing=self._framing_for_theme(concept.theme),
                    camera_movement=self._movement_for_theme(concept.theme),
                    lighting=self._lighting_for_theme(concept.theme),
                    dialogue=self._dialogue_for_theme(concept.theme, i),
                    audio_plan=self._audio_for_theme(concept.theme),
                    positive_prompt=self._positive_prompt(concept, i),
                    negative_prompt=self._negative_prompt(concept.theme),
                    first_frame_continuity="",
                    last_frame_continuity="",
                    generation_model="",
                    model_settings={},
                )
            )

        # Generate dialogue summary
        dialogue_summary = self._summarize_dialogue(scenes)

        # Publishing metadata
        publishing_metadata = {
            "status": StoryStatus.IDEA.name,
            "content_class": concept.content_class,
            "series_id": concept.series_id,
            "episode_id": concept.episode_id,
            "target_duration": concept.target_duration,
            "audience": concept.target_audience,
        }

        return ScriptOutput(
            story_id=concept.story_id,
            episode_id=concept.episode_id,
            concept=concept,
            scenes=scenes,
            dialogue_summary=dialogue_summary,
            estimated_duration=concept.target_duration,
            publishing_metadata=publishing_metadata,
        )

    def _env_for_theme(self, theme: str) -> str:
        """Environment based on story theme."""
        environments = {
            "dreams": "psychic landscape",
            "cinematic_action": "urban rooftop",
            "fantasy_adventures": "enchanted forest",
            "cyberpunk_stories": "neo-city alleyway",
            "martial_arts": "training dojo",
            "comedy_shorts": "friendly café",
            "character_relationships": "living room",
            "sci_fi_exploration": "space station corridor",
            "ai_filmmaking": "production studio",
            "original_story": "various",
        }
        return environments.get(theme, "generic location")

    def _action_for_theme(self, theme: str) -> str:
        """Subject action based on story theme."""
        actions = {
            "dreams": "exploring surreal imagery",
            "cinematic_action": "engaging in chase",
            "fantasy_adventures": "embarking on quest",
            "cyberpunk_stories": "hacking terminal",
            "martial_arts": "practicing form",
            "comedy_shorts": "misunderstanding situation",
            "character_relationships": "heartfelt conversation",
            "sci_fi_exploration": "investigating anomaly",
            "ai_filmmaking": "reviewing footage",
            "original_story": "unfolding narrative",
        }
        return actions.get(theme, "developing story")

    def _framing_for_theme(self, theme: str) -> str:
        """Camera framing based on story theme."""
        framings = {
            "dreams": "slow zoom in",
            "cinematic_action": "dynamic tracking",
            "fantasy_adventures": "wide establishing",
            "cyberpunk_stories": "Dutch angle",
            "martial_arts": "medium close-up",
            "comedy_shorts": "loose framing",
            "character_relationships": "two-shot",
            "sci_fi_exploration": "point-of-view",
            "ai_filmmaking": "reverse angle",
            "original_story": "standard coverage",
        }
        return framings.get(theme, "standard framing")

    def _movement_for_theme(self, theme: str) -> str:
        """Camera movement based on story theme."""
        movements = {
            "dreams": "slow dolly",
            "cinematic_action": "rapid pan",
            "fantasy_adventures": "steady tracking",
            "cyberpunk_stories": "jerky handheld",
            "martial_arts": "static with cuts",
            "comedy_shorts": "jump cut",
            "character_relationships": "slow push-in",
            "sci_fi_exploration": "gliding",
            "ai_filmmaking": "steady cam",
            "original_story": "match cut",
        }
        return movements.get(theme, "static")

    def _lighting_for_theme(self, theme: str) -> str:
        """Lighting based on story theme."""
        lightings = {
            "dreams": "soft, diffused",
            "cinematic_action": "high contrast",
            "fantasy_adventures": "golden hour",
            "cyberpunk_stories": "neon, blue wash",
            "martial_arts": "dynamic, directional",
            "comedy_shorts": "even, flat",
            "character_relationships": "warm, intimate",
            "sci_fi_exploration": "cool, sterile",
            "ai_filmmaking": "neutral, even",
            "original_story": "three-point",
        }
        return lightings.get(theme, "standard")

    def _dialogue_for_theme(self, theme: str, scene_idx: int) -> str:
        """Dialogue based on story theme and scene index."""
        dialogue_themes = {
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
            "ai_filmmaking": [
                "The render's failing again.",
                "We need another take with different lighting.",
            ],
            "original_story": [
                "And so the journey begins.",
                "Nothing will ever be the same.",
            ],
        }
        themes = dialogue_themes.get(theme, ["..."])
        return themes[scene_idx % len(themes)] if themes else "..."

    def _audio_for_theme(self, theme: str) -> str:
        """Audio plan based on story theme."""
        audio_plans = {
            "dreams": "ambient soundscape, soft bells",
            "cinematic_action": "orchestral score, driving percussion",
            "fantasy_adventures": "orchestral theme with choir",
            "cyberpunk_stories": "synthesized bass, glitch effects",
            "martial_arts": "traditional drums, rhythmic strikes",
            "comedy_shorts": "pizzicato strings, humorous stabs",
            "character_relationships": "piano, gentle arpeggios",
            "sci_fi_exploration": "synthesized pads, atmospheric",
            "ai_filmmaking": "digital beeps, process sounds",
            "original_story": "full orchestral score",
        }
        return audio_plans.get(theme, "background music")

    def _positive_prompt(self, concept: StoryConcept, scene_idx: int) -> str:
        """Positive prompt based on story concept and scene."""
        # Simplified: return theme-based prompt fragment
        return f"{concept.theme} style, {concept.content_class.lower()}, {concept.character_focus[0] if concept.character_focus else 'character'} central"

    def _negative_prompt(self, theme: str) -> str:
        """Negative prompt based on story theme (from Spec #9)."""
        negative_prompts = {
            "dreams": "unwanted facial identity changes, costume drift",
            "cinematic_action": "incorrect anatomy, extra fingers",
            "fantasy_adventures": "broken hands, floating objects",
            "cyberpunk_stories": "unwanted logos, text artifacts",
            "martial_arts": "distorted backgrounds, temporal flicker",
            "comedy_shorts": "missing accessories, inconsistent lighting",
            "character_relationships": "unexpected characters",
            "sci_fi_exploration": "unrequested logos",
            "ai_filmmaking": "accidental text artifacts",
            "original_story": "unwanted characters",
        }
        return negative_prompts.get(theme, "unwanted facial identity changes, costume drift")

    def _summarize_dialogue(self, scenes: list[ScriptScene]) -> str:
        """Summarize the dialogue across all scenes."""
        key_lines = [s.dialogue for s in scenes if s.dialogue]
        if not key_lines:
            return "No dialogue generated."
        return " | ".join(key_lines[:3])

    def get_status(self) -> AgentAction:
        """Return agent status action."""
        return AgentAction(
            agent=self.AGENT_ID,
            action="status_check",
            status="ready",
            data={"agent": self.AGENT_NAME, "capability": "script_generation"},
        )


# Module-level agent instance
agent = StoryWriterAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> AgentAction:
    """Execute a Story Writer agent action.

    Convenience function for running agent actions from API or workflow orchestration.

    Args:
        action: The action to execute (e.g., "generate_concept", "generate_script")
        **kwargs: Arguments specific to the action

    Returns:
        AgentAction with standardized output format
    """
    agent_obj = agent

    if action == "generate_concept":
        series_id = kwargs.get("series_id", "series_default")
        episode_id = kwargs.get("episode_id", "ep_default")
        content_class = kwargs.get("content_class", "B")
        character_ids = kwargs.get("character_ids", ["lalin"])
        theme_hint = kwargs.get("theme_hint", "")

        concept = agent_obj.generate_story_concept(
            series_id=series_id,
            episode_id=episode_id,
            content_class=content_class,
            character_ids=character_ids,
            theme_hint=theme_hint,
        )

        return AgentAction(
            agent=agent_obj.AGENT_ID,
            action="generate_concept",
            status="completed",
            data={"story_concept": {
                "story_id": concept.story_id,
                "series_id": concept.series_id,
                "episode_id": concept.episode_id,
                "title": concept.title,
                "theme": concept.theme,
                "tone": concept.tone,
                "character_focus": concept.character_focus,
                "content_class": concept.content_class,
            }},
        )

    elif action == "generate_script":
        kwargs.get("concept_id", "")
        scene_count = kwargs.get("scene_count", 5)

        # In a full implementation, we'd look up the concept by ID
        # For now, generate a default concept and script
        concept = agent_obj.generate_story_concept(
            series_id="series_default",
            episode_id="ep_default",
            content_class="B",
            character_ids=["lalin"],
        )

        script = agent_obj.generate_script(concept, scene_count=scene_count)

        return AgentAction(
            agent=agent_obj.AGENT_ID,
            action="generate_script",
            status="completed",
            data={
                "script_output": {
                    "story_id": script.story_id,
                    "episode_id": script.episode_id,
                    "estimated_duration": script.estimated_duration,
                    "scene_count": len(script.scenes),
                    "dialogue_summary": script.dialogue_summary,
                    "publishing_metadata": script.publishing_metadata,
                    "scenes": [
                        {
                            "scene_id": s.scene_id,
                            "time_range": s.time_range,
                            "characters": s.characters,
                            "environment": s.environment,
                            "subject_action": s.subject_action,
                            "camera_framing": s.camera_framing,
                            "camera_movement": s.camera_movement,
                            "lighting": s.lighting,
                            "dialogue": s.dialogue,
                            "positive_prompt": s.positive_prompt,
                            "negative_prompt": s.negative_prompt,
                        }
                        for s in script.scenes
                    ],
                }
            },
        )

    elif action == "get_status":
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
    "StoryWriterAgent",
    "StoryConcept",
    "ScriptScene",
    "ScriptOutput",
    "AgentAction",
    "execute_action",
    "agent",
]