"""Agent 02 -- Creative Director

Defines series, themes, episode concepts and artistic direction for ZEAZVERSE
per Specification Section 6.

Responsibilities:
- Define series concepts with titles, themes, and target audiences
- Create episode concepts with story arcs and character assignments
- Establish artistic direction and visual style guidelines
- Maintain series bible with canonical story elements
- Validate episode concepts against character bibles and brand identity

Agent Outputs:
- series_definition: Series title, description, theme, character roster
- theme_concept: Theme name, visual style, mood, color palette reference
- episode_outline: Episode title, synopsis, scenes, characters, duration
- artistic_direction: Visual references, style notes, brand alignment
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class SeriesStatus(Enum):
    """Series lifecycle status."""
    IDEA = auto()
    APPROVED = auto()
    IN_PRODUCTION = auto()
    COMPLETED = auto()
    CANCELLED = auto()


class ThemeType(Enum):
    """Content theme classification per Spec #7."""
    CHARACTER_INTRODUCTION = auto()
    CINEMATIC_ACTION = auto()
    FANTASY_ADVENTURES = auto()
    CYBERPUNK_STORIES = auto()
    MARTIAL_ARTS = auto()
    COMEDY_SHORTS = auto()
    CHARACTER_RELATIONSHIPS = auto()
    SCI_FI_EXPLORATION = auto()
    AI_FILMMAKING_BEHIND_SCENES = auto()
    ORIGINAL_SERIALIZED_EPISODES = auto()


class EpisodeStatus(Enum):
    """Episode development status."""
    CONCEPT = auto()
    OUTLINE_APPROVED = auto()
    SCRIPT_APPROVED = auto()
    IN_PRODUCTION = auto()
    COMPLETED = auto()
    BLOCKED = auto()


@dataclass
class SeriesDefinition:
    """Definition of a ZEAZVERSE series."""
    series_id: str
    title: str
    description: str
    theme: ThemeType
    character_ids: list[str]
    target_audience: str
    status: SeriesStatus
    episode_count: int = 0
    created_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class ThemeConcept:
    """Artistic theme concept for a series or episode."""
    theme_id: str
    theme_type: ThemeType
    name: str
    visual_style: str
    mood: str
    color_palette: list[str]  # Brand palette references
    brand_alignment: str  # How it fits ZEAZVERSE brand
    created_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class EpisodeOutline:
    """Episode outline per Spec #8 story framework."""
    episode_id: str
    series_id: str
    title: str
    synopsis: str
    theme_type: ThemeType
    character_ids: list[str]
    target_duration_seconds: int
    story_hook: str  # 0-3 seconds
    setting_conflict: str  # 3-8 seconds
    action_discovery: str  # 8-16 seconds
    escalation_climax: str  # 16-24 seconds
    resolution_twist: str  # 24-30 seconds
    status: EpisodeStatus
    created_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class ArtisticDirection:
    """Artistic direction and style guidelines."""
    direction_id: str
    series_id: str
    visual_references: list[str]
    style_notes: str
    brand_palette: list[str]  # Electric Purple, Neon Magenta, etc.
    character_consistency_rules: list[str]
    negative_prompt_elements: list[str]
    created_at: str = field(default_factory=lambda: uuid4().hex[:12])


class CreativeDirectorAgent:
    """Agent 02 -- Creative Director implementation."""

    AGENT_ID = "AGENT_02"
    AGENT_NAME = "Creative Director"
    DESCRIPTION = "Defines series, themes, episode concepts and artistic direction"

    ZEAZVERSE_BRAND_PALETTE = [
        "#8B5CF6",  # Electric Purple
        "#EC4899",  # Neon Magenta
        "#06B6D4",  # Cyber Blue
        "#070B1D",  # Midnight Navy
        "#F8FAFC",  # Soft White
    ]

    NEGATIVE_PROMPT_ELEMENTS = [
        "unwanted facial identity changes",
        "costume drift",
        "incorrect anatomy",
        "extra fingers",
        "extra limbs",
        "broken hands",
        "floating objects",
        "unnatural physical motion",
        "temporal flicker",
        "missing accessories",
        "inconsistent lighting",
        "distorted backgrounds",
        "accidental text artifacts",
        "unexpected characters",
        "unrequested logos",
    ]

    def __init__(self) -> None:
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID

    def define_series(
        self, title: str, description: str, theme: ThemeType,
        character_ids: list[str], target_audience: str,
    ) -> SeriesDefinition:
        """Define a new ZEAZVERSE series."""
        series_id = f"series_{uuid4().hex[:8]}"

        return SeriesDefinition(
            series_id=series_id,
            title=title,
            description=description,
            theme=theme,
            character_ids=character_ids,
            target_audience=target_audience,
            status=SeriesStatus.IDEA,
            created_at=uuid4().hex[:12],
        )

    def create_theme_concept(
        self, theme_type: ThemeType, name: str,
        visual_style: str, mood: str, brand_alignment: str,
    ) -> ThemeConcept:
        """Create an artistic theme concept."""
        theme_id = f"theme_{uuid4().hex[:8]}"

        return ThemeConcept(
            theme_id=theme_id,
            theme_type=theme_type,
            name=name,
            visual_style=visual_style,
            mood=mood,
            color_palette=list(self.ZEAZVERSE_BRAND_PALETTE),
            brand_alignment=brand_alignment,
            created_at=uuid4().hex[:12],
        )

    def outline_episode(
        self, series_id: str, title: str, synopsis: str,
        theme_type: ThemeType, character_ids: list[str],
        target_duration_seconds: int = 30,
    ) -> EpisodeOutline:
        """Create an episode outline following Spec #8 story framework."""
        episode_id = f"episode_{uuid4().hex[:8]}"

        # Build story framework per Spec #8:
        # 0-3s: Strong visual hook
        # 3-8s: Introduce setting or conflict
        # 8-16s: Character action or discovery
        # 16-24s: Escalation or cinematic climax
        # 24-30s: Resolution, twist or cliffhanger

        return EpisodeOutline(
            episode_id=episode_id,
            series_id=series_id,
            title=title,
            synopsis=synopsis,
            theme_type=theme_type,
            character_ids=character_ids,
            target_duration_seconds=target_duration_seconds,
            story_hook="",
            setting_conflict="",
            action_discovery="",
            escalation_climax="",
            resolution_twist="",
            status=EpisodeStatus.CONCEPT,
            created_at=uuid4().hex[:12],
        )

    def define_artistic_direction(
        self, series_id: str, visual_references: list[str],
        style_notes: str, character_consistency_rules: list[str],
    ) -> ArtisticDirection:
        """Define artistic direction for a series."""
        direction_id = f"direction_{uuid4().hex[:8]}"

        return ArtisticDirection(
            direction_id=direction_id,
            series_id=series_id,
            visual_references=visual_references,
            style_notes=style_notes,
            brand_palette=list(self.ZEAZVERSE_BRAND_PALETTE),
            character_consistency_rules=character_consistency_rules,
            negative_prompt_elements=list(self.NEGATIVE_PROMPT_ELEMENTS),
            created_at=uuid4().hex[:12],
        )

    def validate_episode_concept(
        self, episode_outline: EpisodeOutline,
        character_bibles: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate episode concept against character bibles and brand."""
        issues = []
        warnings = []

        # Check character references exist in bibles
        for cid in episode_outline.character_ids:
            if cid.upper() not in ["LALIN", "NICHA", "PIM", "YADA"]:
                issues.append(f"Unknown character reference: {cid}")
            elif cid not in character_bibles:
                warnings.append(f"No character bible on file for: {cid}")

        # Check duration aligns with Spec #8 default (30 seconds)
        if episode_outline.target_duration_seconds != 30:
            warnings.append(
                f"Duration {episode_outline.target_duration_seconds}s "
                f"differs from Spec #8 default of 30s"
            )

        # Check theme has story framework sections populated
        if not episode_outline.story_hook:
            warnings.append("Story hook (0-3s) not yet defined")
        if not episode_outline.setting_conflict:
            warnings.append("Setting/conflict (3-8s) not yet defined")
        if not episode_outline.action_discovery:
            warnings.append("Action/discovery (8-16s) not yet defined")
        if not episode_outline.escalation_climax:
            warnings.append("Escalation/climax (16-24s) not yet defined")
        if not episode_outline.resolution_twist:
            warnings.append("Resolution/twist (24-30s) not yet defined")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "episode_id": episode_outline.episode_id,
        }

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "capability": "creative_direction",
            "themes_supported": [t.name for t in ThemeType],
        }


# Module-level agent instance
agent = CreativeDirectorAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a Creative Director Agent action.

    Convenience function for running agent actions from API or workflow orchestration.

    Args:
        action: The action to execute (e.g., "define_series", "outline_episode",
               "create_theme_concept", "define_artistic_direction",
               "validate_episode_concept", "status_check")
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "define_series":
        series = agent_obj.define_series(
            title=kwargs.get("title", "Untitled Series"),
            description=kwargs.get("description", ""),
            theme=ThemeType[kwargs.get("theme", "ORIGINAL_SERIALIZED_EPISODES")],
            character_ids=kwargs.get("character_ids", ["lalin"]),
            target_audience=kwargs.get("target_audience", "Global"),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "define_series",
            "status": "completed",
            "series_id": series.series_id,
            "title": series.title,
            "description": series.description,
            "theme": series.theme.name,
            "character_ids": series.character_ids,
            "target_audience": series.target_audience,
            "series_status": series.status.name,
            "created_at": series.created_at,
        }

    elif action == "create_theme_concept":
        concept = agent_obj.create_theme_concept(
            theme_type=ThemeType[kwargs.get("theme_type", "ORIGINAL_SERIALIZED_EPISODES")],
            name=kwargs.get("name", "Untitled Theme"),
            visual_style=kwargs.get("visual_style", ""),
            mood=kwargs.get("mood", ""),
            brand_alignment=kwargs.get("brand_alignment", ""),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "create_theme_concept",
            "status": "completed",
            "theme_id": concept.theme_id,
            "theme_type": concept.theme_type.name,
            "name": concept.name,
            "visual_style": concept.visual_style,
            "mood": concept.mood,
            "color_palette": concept.color_palette,
            "brand_alignment": concept.brand_alignment,
            "created_at": concept.created_at,
        }

    elif action == "outline_episode":
        outline = agent_obj.outline_episode(
            series_id=kwargs.get("series_id", "series_default"),
            title=kwargs.get("title", "Untitled Episode"),
            synopsis=kwargs.get("synopsis", ""),
            theme_type=ThemeType[kwargs.get("theme_type", "ORIGINAL_SERIALIZED_EPISODES")],
            character_ids=kwargs.get("character_ids", ["lalin"]),
            target_duration_seconds=kwargs.get("target_duration_seconds", 30),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "outline_episode",
            "status": "completed",
            "episode_id": outline.episode_id,
            "series_id": outline.series_id,
            "title": outline.title,
            "synopsis": outline.synopsis,
            "theme_type": outline.theme_type.name,
            "character_ids": outline.character_ids,
            "target_duration_seconds": outline.target_duration_seconds,
            "story_framework": {
                "0-3s_hook": outline.story_hook,
                "3-8s_setting_conflict": outline.setting_conflict,
                "8-16s_action_discovery": outline.action_discovery,
                "16-24s_escalation_climax": outline.escalation_climax,
                "24-30s_resolution_twist": outline.resolution_twist,
            },
            "episode_status": outline.status.name,
            "created_at": outline.created_at,
        }

    elif action == "define_artistic_direction":
        direction = agent_obj.define_artistic_direction(
            series_id=kwargs.get("series_id", "series_default"),
            visual_references=kwargs.get("visual_references", []),
            style_notes=kwargs.get("style_notes", ""),
            character_consistency_rules=kwargs.get(
                "character_consistency_rules", []
            ),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "define_artistic_direction",
            "status": "completed",
            "direction_id": direction.direction_id,
            "series_id": direction.series_id,
            "visual_references": direction.visual_references,
            "style_notes": direction.style_notes,
            "brand_palette": direction.brand_palette,
            "character_consistency_rules": direction.character_consistency_rules,
            "negative_prompt_elements": direction.negative_prompt_elements,
            "created_at": direction.created_at,
        }

    elif action == "validate_episode_concept":
        # Build a minimal EpisodeOutline from kwargs for validation
        outline = EpisodeOutline(
            episode_id=kwargs.get("episode_id", f"episode_{uuid4().hex[:6]}"),
            series_id=kwargs.get("series_id", "series_default"),
            title=kwargs.get("title", "Untitled"),
            synopsis=kwargs.get("synopsis", ""),
            theme_type=ThemeType[kwargs.get("theme_type", "ORIGINAL_SERIALIZED_EPISODES")],
            character_ids=kwargs.get("character_ids", ["lalin"]),
            target_duration_seconds=kwargs.get("target_duration_seconds", 30),
            story_hook=kwargs.get("story_hook", ""),
            setting_conflict=kwargs.get("setting_conflict", ""),
            action_discovery=kwargs.get("action_discovery", ""),
            escalation_climax=kwargs.get("escalation_climax", ""),
            resolution_twist=kwargs.get("resolution_twist", ""),
            status=EpisodeStatus.CONCEPT,
        )
        validation = agent_obj.validate_episode_concept(
            outline, kwargs.get("character_bibles", {})
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "validate_episode_concept",
            "status": "completed",
            "episode_id": validation["episode_id"],
            "valid": validation["valid"],
            "issues": validation["issues"],
            "warnings": validation["warnings"],
        }

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "CreativeDirectorAgent",
    "SeriesDefinition",
    "ThemeConcept",
    "EpisodeOutline",
    "ArtisticDirection",
    "SeriesStatus",
    "ThemeType",
    "EpisodeStatus",
    "execute_action",
    "agent",
]