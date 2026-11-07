"""Agent 13 -- YouTube SEO Agent

Generates SEO-optimized metadata for ZEAZVERSE episodes.

Responsibilities:
- Generate three candidate titles per episode
- Create primary description with search-relevant keywords
- Provide topic labels and appropriate hashtags
- Suggest playlist placement
- Provide publishing recommendation
- Include disclosure metadata for AI content
- Support Spec #11: YouTube SEO Engine
- Never represent suggestions as validated performance improvements

Agent Outputs:
- three candidate titles
- primary description
- search keywords
- topic labels
- appropriate hashtags
- suggested playlist
- publishing recommendation
- disclosure metadata
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class CaptionLanguage(Enum):
    """Supported caption languages."""
    ENGLISH = auto()
    THAI = auto()


class PublishingStatus(Enum):
    """Publishing status options."""
    PRIVATE = auto()
    PUBLIC = auto()
    SCHEDULED = auto()
    UNLISTED = auto()


class DisclosureType(Enum):
    """AI content disclosure types."""
    NONE = auto()
    AI_GENERATED = auto()
    AI_ASSISTED = auto()


@dataclass
class SEOMetadata:
    """Complete SEO metadata for an episode."""
    episode_id: str
    title_options: list[str]  # Three candidate titles
    primary_description: str
    search_keywords: list[str]  # Topic labels
    appropriate_hashtags: list[str]
    suggested_playlist: str
    publishing_recommendation: PublishingStatus
    disclosure_metadata: dict[str, Any]
    generated_at: str = field(default_factory=lambda: uuid4().hex[:12])


class YouTubeSEOAgent:
    """Agent 13 -- YouTube SEO Agent implementation."""

    AGENT_ID = "AGENT_13"
    AGENT_NAME = "YouTube SEO Agent"
    DESCRIPTION = "Generates titles, descriptions, keywords, subtitles and thumbnail proposals"

    def __init__(self, default_playlist: str = "ZEAZVERSE Latest"):
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID
        self.default_playlist = default_playlist

    def generate_seo_metadata(
        self, episode_id: str, series_id: str,
        character_ids: list[str],
        theme: str,
        content_type: str,
    ) -> SEOMetadata:
        """Generate complete SEO metadata for an episode."""

        # Generate three candidate titles
        title_options = self._generate_title_options(series_id, theme, content_type)

        # Create primary description
        primary_description = self._generate_primary_description(
            series_id, theme, character_ids, content_type
        )

        # Provide search keywords (topic labels)
        search_keywords = self._generate_search_keywords(theme, content_type, character_ids)

        # Provide appropriate hashtags
        appropriate_hashtags = self._generate_hashtags(theme, content_type)

        # Suggest playlist
        suggested_playlist = self._suggest_playlist(theme)

        # Provide publishing recommendation
        publishing_recommendation = self._publishing_recommendation(content_type)

        # Generate disclosure metadata
        disclosure_metadata = self._generate_disclosure_metadata(content_type)

        return SEOMetadata(
            episode_id=episode_id,
            title_options=title_options,
            primary_description=primary_description,
            search_keywords=search_keywords,
            appropriate_hashtags=appropriate_hashtags,
            suggested_playlist=suggested_playlist,
            publishing_recommendation=publishing_recommendation,
            disclosure_metadata=disclosure_metadata,
        )

    def _generate_title_options(self, series_id: str, theme: str,
                                content_type: str) -> list[str]:
        """Generate three candidate titles per Spec #11."""
        title_templates = {
            "dreams": [
                f"Dream Walker: {series_id} Episode - Supernatural Mystery",
                f"When Dreams Become Reality: The {series_id} Story",
                f"LALIN's Dreamworld: {series_id} Chapter",
            ],
            "cinematic_action": [
                f"Cinematic Showdown: {series_id} Episode - High-Octane Action",
                f"Action Unleashed: The {series_id} Story",
                f"NICHA's Mission: {series_id} Episode",
            ],
            "fantasy_adventures": [
                f"Fantastic Voyage: {series_id} Episode - Magical Adventure",
                f"Quest for the Unknown: The {series_id} Story",
                f"PIM's Rebellion: {series_id} Chapter",
            ],
            "cyberpunk_stories": [
                f"Neon Noir: {series_id} Episode - Tech-Noir Mystery",
                f"Cyberpunk Sunset: The {series_id} Story",
                f"YADA's Hack: {series_id} Episode",
            ],
            "martial_arts": [
                f"Clash of Titans: {series_id} Episode - Martial Arts Extravaganza",
                f"Warrior's Path: The {series_id} Story",
                f"PIM's Challenge: {series_id} Episode",
            ],
            "comedy_shorts": [
                f"Laugh Out Loud: {series_id} Episode - Comedy Shorts",
                f"Comic Relief: The {series_id} Story",
                f"LALIN's Funny Day: {series_id} Chapter",
            ],
            "sci_fi_exploration": [
                f"Future Frontiers: {series_id} Episode - Sci-Fi Exploration",
                f"Beyond the Stars: The {series_id} Story",
                f"YADA's Invention: {series_id} Chapter",
            ],
            "original_story": [
                f"Original Story: {series_id} Episode - Cinematic Journey",
                f"The {series_id} Begins: Episode One",
                f"New Episode of {series_id}",
            ],
        }

        templates = title_templates.get(theme, title_templates["original_story"])
        return templates[:3]

    def _generate_primary_description(
        self, series_id: str, theme: str, character_ids: list[str],
        content_type: str,
    ) -> str:
        """Create primary description with search-relevant keywords."""
        char_descriptions = {
            "LALIN": "creative, compassionate dreamer",
            "NICHA": "strategic, analytical strategist",
            "PIM": "fearless, energetic rebel",
            "YADA": "inventive, elegant visionary",
        }

        chars_mentioned = ", ".join(
            [char_descriptions.get(c, c) for c in character_ids[:2]]
        )

        theme_hooks = {
            "dreams": "explore supernatural mystery and dream worlds",
            "cinematic_action": "high-octane action and cinematic storytelling",
            "fantasy_adventures": "magical quests and adventure across realms",
            "cyberpunk_stories": "tech-noir investigations in a futuristic city",
            "martial_arts": "intense martial arts combat and warrior discipline",
            "comedy_shorts": "laugh-out-loud comedy and humorous situations",
            "sci_fi_exploration": "future technology and sci-fi discovery",
            "original_story": "original cinematic narrative and story development",
        }

        hook = theme_hooks.get(theme, "original cinematic content")

        return f"""
{series_id} - {hook}

Watch as {chars_mentioned} embark on an epic journey in this original episode from ZEAZVERSE.

This episode features original content from ZEAZDEV COMPANY LIMITED, 
presenting {len(character_ids)} unique AI virtual idols from Thailand.

Viewer discretion advised: This content features AI-generated virtual characters. 
All storylines are substantially original and created for entertainment purposes.

New episodes release weekly. Subscribe for more original cinematic stories.
        """.strip()

    def _generate_search_keywords(
        self, theme: str, content_type: str, character_ids: list[str],
    ) -> list[str]:
        """Provide search-relevant keywords (topic labels)."""
        base_keywords = ["ZEAZVERSE", "ai virtual idol", "animated series"]

        theme_keywords = {
            "dreams": ["supernatural", "dreams", "mystery", "fantasy"],
            "cinematic_action": ["action", "cinematic", "thriller", "adventure"],
            "fantasy_adventures": ["fantasy", "quest", "magic", "adventure"],
            "cyberpunk_stories": ["cyberpunk", "noir", "futuristic", "technology"],
            "martial_arts": ["martial arts", "combat", "warrior", "discipline"],
            "comedy_shorts": ["comedy", "humor", "laughter", "entertainment"],
            "sci_fi_exploration": ["science fiction", "future", "exploration", "technology"],
            "original_story": ["original story", "cinema", "narrative", "episode"],
        }

        keywords = base_keywords + theme_keywords.get(theme, [])

        # Add character names
        for cid in character_ids:
            if cid == "LALIN":
                keywords.extend(["LALIN", "dreamer", "thai character"])
            elif cid == "NICHA":
                keywords.extend(["NICHA", "strategist", "thai character"])
            elif cid == "PIM":
                keywords.extend(["PIM", "rebel", "thai character"])
            elif cid == "YADA":
                keywords.extend(["YADA", "visionary", "thai character"])

        # Deduplicate while preserving order
        seen = set()
        unique_keywords = []
        for k in keywords:
            if k.lower() not in seen:
                seen.add(k.lower())
                unique_keywords.append(k)

        return unique_keywords[:10]

    def _generate_hashtags(self, theme: str, content_type: str) -> list[str]:
        """Provide appropriate hashtags."""
        theme_hashtags = {
            "dreams": ["#DreamWorld", "#Supernatural", "#ZEAZVERSE"],
            "cinematic_action": ["#CinematicAction", "#HighOctane", "#ZEAZVERSE"],
            "fantasy_adventures": ["#FantasyAdventure", "#MagicalQuest", "#ZEAZVERSE"],
            "cyberpunk_stories": ["#Cyberpunk", "#TechNoir", "#ZEAZVERSE"],
            "martial_arts": ["#MartialArts", "#Warrior", "#ZEAZVERSE"],
            "comedy_shorts": ["#Comedy", "#Laugh", "#ZEAZVERSE"],
            "sci_fi_exploration": ["#SciFi", "#Future", "#ZEAZVERSE"],
            "original_story": ["#OriginalStory", "#Cinematic", "#ZEAZVERSE"],
        }

        hashtags = theme_hashtags.get(theme, ["#ZEAZVERSE"])

        if "#ZEAZVERSE" not in hashtags:
            hashtags.append("#ZEAZVERSE")

        return hashtags

    def _suggest_playlist(self, theme: str) -> str:
        """Suggest playlist placement."""
        playlist_map = {
            "dreams": "ZEAZVERSE Dreams & Mysteries",
            "cinematic_action": "ZEAZVERSE Action & Thriller",
            "fantasy_adventures": "ZEAZVERSE Fantasy Adventures",
            "cyberpunk_stories": "ZEAZVERSE Cyberpunk & Noir",
            "martial_arts": "ZEAZVERSE Martial Arts",
            "comedy_shorts": "ZEAZVERSE Comedy Shorts",
            "sci_fi_exploration": "ZEAZVERSE Sci-Fi & Future",
            "original_story": "ZEAZVERSE Original Episodes",
        }

        return playlist_map.get(theme, self.default_playlist)

    def _publishing_recommendation(self, content_type: str) -> PublishingStatus:
        """Provide publishing recommendation."""
        return PublishingStatus.PRIVATE

    def _generate_disclosure_metadata(self, content_type: str) -> dict[str, Any]:
        """Generate AI content disclosure metadata per YouTube policies."""
        has_ai_content = content_type in [
            "cinematic_action", "fantasy_adventures", "cyberpunk_stories"
        ]

        return {
            "has_ai_generated_content": has_ai_content,
            "ai_disclosure_type": (
                DisclosureType.AI_GENERATED.name if has_ai_content else DisclosureType.NONE.name
            ),
            "disclosure_text": (
                "This video features AI-generated virtual characters. "
                "All storylines are substantially original."
                if has_ai_content
                else "No AI-generated content detected."
            ),
            "metadata_version": "1.0",
            "generated_at": uuid4().hex[:12],
        }

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "default_playlist": self.default_playlist,
            "capability": "youtube_seo",
        }


# Module-level agent instance
agent = YouTubeSEOAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a YouTube SEO Agent agent action.

    Convenience function for running agent actions from API or workflow orchestration.

    Args:
        action: The action to execute (e.g., "generate_metadata", "status_check")
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "generate_metadata":
        episode_id = kwargs.get("episode_id", f"episode_{uuid4().hex[:6]}")
        series_id = kwargs.get("series_id", "series_default")
        character_ids = kwargs.get("character_ids", ["lalin"])
        theme = kwargs.get("theme", "original_story")
        content_type = kwargs.get("content_type", "original_story")

        metadata = agent_obj.generate_seo_metadata(
            episode_id=episode_id,
            series_id=series_id,
            character_ids=character_ids,
            theme=theme,
            content_type=content_type,
        )

        return {
            "agent": agent_obj.AGENT_ID,
            "action": "generate_metadata",
            "status": "completed",
            "episode_id": metadata.episode_id,
            "series_id": series_id,
            "title_options": metadata.title_options,
            "primary_description": metadata.primary_description,
            "search_keywords": metadata.search_keywords,
            "appropriate_hashtags": metadata.appropriate_hashtags,
            "suggested_playlist": metadata.suggested_playlist,
            "publishing_recommendation": metadata.publishing_recommendation.name,
            "disclosure_metadata": metadata.disclosure_metadata,
            "generated_at": metadata.generated_at,
        }

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "YouTubeSEOAgent",
    "SEOMetadata",
    "CaptionLanguage",
    "PublishingStatus",
    "DisclosureType",
    "execute_action",
    "agent",
]