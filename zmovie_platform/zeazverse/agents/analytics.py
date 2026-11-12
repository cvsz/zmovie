"""Agent 16 -- Analytics Agent

Collects authorized performance data per Spec #19.

Responsibilities:
- Collect views, engaged views, watch time, average view duration
- Track audience retention, subscribers gained, traffic sources
- Monitor viewer geography, returning viewers, episode performance
- Track character performance metrics
- Use authorized YouTube reporting data only
- Never claim monetization approval merely because thresholds are met

Agent Outputs:
- analytics_snapshot: Performance metrics for a time period
- episode_performance: Per-episode metrics
- character_performance: Per-character engagement metrics
- audience_insights: Demographics and retention data
- monetization_readiness: Honest assessment (not a guarantee)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class MetricType(Enum):
    """Types of analytics metrics."""
    VIEWS = auto()
    ENGAGED_VIEWS = auto()
    WATCH_TIME = auto()
    AVERAGE_VIEW_DURATION = auto()
    AUDIENCE_RETENTION = auto()
    SUBSCRIBERS_GAINED = auto()
    TRAFFIC_SOURCES = auto()
    VIEWER_GEOGRAPHY = auto()
    RETURNING_VIEWERS = auto()
    EPISODE_PERFORMANCE = auto()
    CHARACTER_PERFORMANCE = auto()


class DataSource(Enum):
    """Authorized data sources."""
    YOUTUBE_ANALYTICS = auto()
    INTERNAL_TRACKING = auto()


@dataclass
class AnalyticsSnapshot:
    """Performance metrics snapshot for a time period."""
    snapshot_id: str
    channel_id: str
    period_start: str
    period_end: str
    data_source: DataSource
    views: int = 0
    engaged_views: int = 0
    watch_time_minutes: float = 0.0
    average_view_duration_seconds: float = 0.0
    audience_retention_percentage: float = 0.0
    subscribers_gained: int = 0
    traffic_sources: dict[str, int] = field(default_factory=dict)
    viewer_geography: dict[str, int] = field(default_factory=dict)
    returning_viewers: int = 0
    collected_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class EpisodePerformance:
    """Performance metrics for a single episode."""
    episode_id: str
    series_id: str
    views: int = 0
    watch_time_minutes: float = 0.0
    average_view_duration_seconds: float = 0.0
    audience_retention_percentage: float = 0.0
    likes: int = 0
    dislikes: int = 0
    comments: int = 0
    shares: int = 0
    subscribers_gained: int = 0
    traffic_sources: dict[str, int] = field(default_factory=dict)
    collected_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class CharacterPerformance:
    """Performance metrics for a character across episodes."""
    character_id: str
    character_name: str
    episodes_featured: int = 0
    total_views: int = 0
    average_views_per_episode: float = 0.0
    total_watch_time_minutes: float = 0.0
    audience_retention_percentage: float = 0.0
    subscriber_impact: int = 0  # Net subscribers attributed to this character
    collected_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class MonetizationReadiness:
    """Honest monetization readiness assessment (not a guarantee)."""
    channel_id: str
    meets_view_threshold: bool
    meets_subscriber_threshold: bool
    meets_watch_time_threshold: bool
    has_community_standings: bool = False  # No strikes, good standing
    has_2fa_enabled: bool = False
    located_in_eligible_country: bool = False
    overall_ready: bool = False
    notes: list[str] = field(default_factory=list)
    assessed_at: str = field(default_factory=lambda: uuid4().hex[:12])


class AnalyticsAgent:
    """Agent 16 -- Analytics Agent implementation."""

    AGENT_ID = "AGENT_16"
    AGENT_NAME = "Analytics Agent"
    DESCRIPTION = "Collects authorized performance data"

    # YouTube Partner Program thresholds (as of specification)
    YPP_SUBSCRIBER_THRESHOLD = 500
    YPP_VIEW_THRESHOLD = 3_000_000  # 3M public views in last 90 days
    YPP_WATCH_TIME_THRESHOLD = 3_000  # 3,000 watch hours in last 90 days
    YPP_SHORT_VIEW_THRESHOLD = 3_000_000  # 3M Shorts views in last 90 days

    def __init__(self):
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID
        self._snapshots: dict[str, AnalyticsSnapshot] = {}
        self._episode_metrics: dict[str, EpisodePerformance] = {}
        self._character_metrics: dict[str, CharacterPerformance] = {}

    def collect_snapshot(
        self, channel_id: str, period_start: str, period_end: str,
        data_source: DataSource = DataSource.YOUTUBE_ANALYTICS,
        metrics: dict[str, Any] | None = None,
    ) -> AnalyticsSnapshot:
        """Collect an analytics snapshot for a time period.

        Only uses authorized YouTube reporting data.
        """
        snapshot_id = f"snapshot_{uuid4().hex[:8]}"
        metrics = metrics or {}

        snapshot = AnalyticsSnapshot(
            snapshot_id=snapshot_id,
            channel_id=channel_id,
            period_start=period_start,
            period_end=period_end,
            data_source=data_source,
            views=metrics.get("views", 0),
            engaged_views=metrics.get("engaged_views", 0),
            watch_time_minutes=metrics.get("watch_time_minutes", 0.0),
            average_view_duration_seconds=metrics.get(
                "average_view_duration_seconds", 0.0
            ),
            audience_retention_percentage=metrics.get(
                "audience_retention_percentage", 0.0
            ),
            subscribers_gained=metrics.get("subscribers_gained", 0),
            traffic_sources=metrics.get("traffic_sources", {}),
            viewer_geography=metrics.get("viewer_geography", {}),
            returning_viewers=metrics.get("returning_viewers", 0),
        )
        self._snapshots[snapshot_id] = snapshot
        return snapshot

    def record_episode_performance(
        self, episode_id: str, series_id: str,
        metrics: dict[str, Any] | None = None,
    ) -> EpisodePerformance:
        """Record performance metrics for a single episode."""
        metrics = metrics or {}

        performance = EpisodePerformance(
            episode_id=episode_id,
            series_id=series_id,
            views=metrics.get("views", 0),
            watch_time_minutes=metrics.get("watch_time_minutes", 0.0),
            average_view_duration_seconds=metrics.get(
                "average_view_duration_seconds", 0.0
            ),
            audience_retention_percentage=metrics.get(
                "audience_retention_percentage", 0.0
            ),
            likes=metrics.get("likes", 0),
            dislikes=metrics.get("dislikes", 0),
            comments=metrics.get("comments", 0),
            shares=metrics.get("shares", 0),
            subscribers_gained=metrics.get("subscribers_gained", 0),
            traffic_sources=metrics.get("traffic_sources", {}),
        )
        self._episode_metrics[episode_id] = performance
        return performance

    def record_character_performance(
        self, character_id: str, character_name: str,
        episodes_featured: int = 0,
        total_views: int = 0,
        subscriber_impact: int = 0,
    ) -> CharacterPerformance:
        """Record performance metrics for a character."""
        performance = CharacterPerformance(
            character_id=character_id,
            character_name=character_name,
            episodes_featured=episodes_featured,
            total_views=total_views,
            average_views_per_episode=(
                total_views / episodes_featured if episodes_featured > 0 else 0.0
            ),
            subscriber_impact=subscriber_impact,
        )
        self._character_metrics[character_id] = performance
        return performance

    def assess_monetization_readiness(
        self, channel_id: str,
        subscriber_count: int,
        public_views_90d: int,
        watch_hours_90d: float,
        shorts_views_90d: int = 0,
        has_community_standings: bool = False,
        has_2fa_enabled: bool = False,
        located_in_eligible_country: bool = False,
    ) -> MonetizationReadiness:
        """Assess monetization readiness honestly.

        Never claims monetization approval merely because thresholds are met.
        Per Spec #19: "Never claim monetization approval merely because
        numerical thresholds are met."
        """
        meets_subscriber = subscriber_count >= self.YPP_SUBSCRIBER_THRESHOLD
        meets_views = public_views_90d >= self.YPP_VIEW_THRESHOLD
        meets_watch_time = watch_hours_90d >= self.YPP_WATCH_TIME_THRESHOLD
        meets_short_views = shorts_views_90d >= self.YPP_SHORT_VIEW_THRESHOLD

        notes = []
        if not meets_subscriber:
            notes.append(
                f"Subscribers {subscriber_count} below threshold "
                f"{self.YPP_SUBSCRIBER_THRESHOLD}"
            )
        if not meets_views and not meets_short_views:
            notes.append(
                f"Public views {public_views_90d} (and Shorts {shorts_views_90d}) "
                f"below threshold {self.YPP_VIEW_THRESHOLD}"
            )
        if not meets_watch_time:
            notes.append(
                f"Watch hours {watch_hours_90d} below threshold "
                f"{self.YPP_WATCH_TIME_THRESHOLD}"
            )
        if not has_community_standings:
            notes.append("Channel not in good community standing")
        if not has_2fa_enabled:
            notes.append("2FA not enabled on account")
        if not located_in_eligible_country:
            notes.append("Account not in YPP-eligible country")

        overall_ready = (
            meets_subscriber
            and (meets_views or meets_short_views)
            and meets_watch_time
            and has_community_standings
            and has_2fa_enabled
            and located_in_eligible_country
        )

        if overall_ready:
            notes.append(
                "Thresholds met - apply for YPP review; approval not guaranteed"
            )

        return MonetizationReadiness(
            channel_id=channel_id,
            meets_view_threshold=meets_views or meets_short_views,
            meets_subscriber_threshold=meets_subscriber,
            meets_watch_time_threshold=meets_watch_time,
            has_community_standings=has_community_standings,
            has_2fa_enabled=has_2fa_enabled,
            located_in_eligible_country=located_in_eligible_country,
            overall_ready=overall_ready,
            notes=notes,
        )

    def get_top_episodes(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top performing episodes by views."""
        episodes = sorted(
            self._episode_metrics.values(),
            key=lambda e: e.views,
            reverse=True,
        )
        return [
            {
                "episode_id": e.episode_id,
                "series_id": e.series_id,
                "views": e.views,
                "watch_time_minutes": e.watch_time_minutes,
                "average_view_duration_seconds": e.average_view_duration_seconds,
                "audience_retention_percentage": e.audience_retention_percentage,
                "likes": e.likes,
                "comments": e.comments,
                "shares": e.shares,
            }
            for e in episodes[:limit]
        ]

    def get_top_characters(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top performing characters by views."""
        characters = sorted(
            self._character_metrics.values(),
            key=lambda c: c.total_views,
            reverse=True,
        )
        return [
            {
                "character_id": c.character_id,
                "character_name": c.character_name,
                "episodes_featured": c.episodes_featured,
                "total_views": c.total_views,
                "average_views_per_episode": c.average_views_per_episode,
                "subscriber_impact": c.subscriber_impact,
            }
            for c in characters[:limit]
        ]

    def get_latest_snapshot(self, channel_id: str) -> AnalyticsSnapshot | None:
        """Get the most recent analytics snapshot for a channel."""
        snapshots = [
            s for s in self._snapshots.values() if s.channel_id == channel_id
        ]
        if not snapshots:
            return None
        return max(snapshots, key=lambda s: s.collected_at)

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "capability": "analytics",
            "snapshots_collected": len(self._snapshots),
            "episodes_tracked": len(self._episode_metrics),
            "characters_tracked": len(self._character_metrics),
            "ypp_thresholds": {
                "subscribers": self.YPP_SUBSCRIBER_THRESHOLD,
                "public_views_90d": self.YPP_VIEW_THRESHOLD,
                "watch_hours_90d": self.YPP_WATCH_TIME_THRESHOLD,
            },
        }


# Module-level agent instance
agent = AnalyticsAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute an Analytics Agent action.

    Args:
        action: The action to execute
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "collect_snapshot":
        snapshot = agent_obj.collect_snapshot(
            channel_id=kwargs.get("channel_id", "channel_default"),
            period_start=kwargs.get("period_start", ""),
            period_end=kwargs.get("period_end", ""),
            data_source=DataSource[kwargs.get("data_source", "YOUTUBE_ANALYTICS")],
            metrics=kwargs.get("metrics", {}),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "collect_snapshot",
            "status": "completed",
            "snapshot_id": snapshot.snapshot_id,
            "channel_id": snapshot.channel_id,
            "period_start": snapshot.period_start,
            "period_end": snapshot.period_end,
            "views": snapshot.views,
            "engaged_views": snapshot.engaged_views,
            "watch_time_minutes": snapshot.watch_time_minutes,
            "average_view_duration_seconds": snapshot.average_view_duration_seconds,
            "audience_retention_percentage": snapshot.audience_retention_percentage,
            "subscribers_gained": snapshot.subscribers_gained,
            "collected_at": snapshot.collected_at,
        }

    elif action == "record_episode_performance":
        performance = agent_obj.record_episode_performance(
            episode_id=kwargs.get("episode_id", ""),
            series_id=kwargs.get("series_id", ""),
            metrics=kwargs.get("metrics", {}),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "record_episode_performance",
            "status": "completed",
            "episode_id": performance.episode_id,
            "views": performance.views,
            "watch_time_minutes": performance.watch_time_minutes,
            "average_view_duration_seconds": performance.average_view_duration_seconds,
            "audience_retention_percentage": performance.audience_retention_percentage,
            "likes": performance.likes,
            "comments": performance.comments,
            "shares": performance.shares,
        }

    elif action == "record_character_performance":
        char_performance = agent_obj.record_character_performance(
            character_id=kwargs.get("character_id", ""),
            character_name=kwargs.get("character_name", ""),
            episodes_featured=kwargs.get("episodes_featured", 0),
            total_views=kwargs.get("total_views", 0),
            subscriber_impact=kwargs.get("subscriber_impact", 0),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "record_character_performance",
            "status": "completed",
            "character_id": char_performance.character_id,
            "character_name": char_performance.character_name,
            "episodes_featured": char_performance.episodes_featured,
            "total_views": char_performance.total_views,
            "average_views_per_episode": char_performance.average_views_per_episode,
            "subscriber_impact": char_performance.subscriber_impact,
        }

    elif action == "assess_monetization_readiness":
        readiness = agent_obj.assess_monetization_readiness(
            channel_id=kwargs.get("channel_id", ""),
            subscriber_count=kwargs.get("subscriber_count", 0),
            public_views_90d=kwargs.get("public_views_90d", 0),
            watch_hours_90d=kwargs.get("watch_hours_90d", 0.0),
            shorts_views_90d=kwargs.get("shorts_views_90d", 0),
            has_community_standings=kwargs.get("has_community_standings", False),
            has_2fa_enabled=kwargs.get("has_2fa_enabled", False),
            located_in_eligible_country=kwargs.get(
                "located_in_eligible_country", False
            ),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "assess_monetization_readiness",
            "status": "completed",
            "channel_id": readiness.channel_id,
            "meets_view_threshold": readiness.meets_view_threshold,
            "meets_subscriber_threshold": readiness.meets_subscriber_threshold,
            "meets_watch_time_threshold": readiness.meets_watch_time_threshold,
            "has_community_standings": readiness.has_community_standings,
            "has_2fa_enabled": readiness.has_2fa_enabled,
            "located_in_eligible_country": readiness.located_in_eligible_country,
            "overall_ready": readiness.overall_ready,
            "notes": readiness.notes,
            "assessed_at": readiness.assessed_at,
        }

    elif action == "get_top_episodes":
        top = agent_obj.get_top_episodes(limit=kwargs.get("limit", 10))
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_top_episodes",
            "status": "completed",
            "episodes": top,
        }

    elif action == "get_top_characters":
        top = agent_obj.get_top_characters(limit=kwargs.get("limit", 10))
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_top_characters",
            "status": "completed",
            "characters": top,
        }

    elif action == "get_latest_snapshot":
        snapshot_data = agent_obj.get_latest_snapshot(
            kwargs.get("channel_id", "channel_default")
        )
        if snapshot_data is None:
            return {
                "agent": agent_obj.AGENT_ID,
                "action": "get_latest_snapshot",
                "status": "blocked",
                "error": "No snapshot found",
            }
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_latest_snapshot",
            "status": "completed",
            "snapshot": snapshot_data,
        }

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "AnalyticsAgent",
    "AnalyticsSnapshot",
    "EpisodePerformance",
    "CharacterPerformance",
    "MonetizationReadiness",
    "MetricType",
    "DataSource",
    "execute_action",
    "agent",
]