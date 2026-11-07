"""Agent 17 -- Growth Experiment Agent

Recommends creative experiments based on actual analytics per Spec #19.

Responsibilities:
- Recommend experiments comparing story concepts, character themes, hooks,
  video length, titles, thumbnails, posting schedules
- Use authorized YouTube reporting data only
- Do not manufacture engagement or use bots to inflate views or subscribers
- Track experiment hypotheses, results, and recommendations

Agent Outputs:
- experiment_design: Hypothesis, variants, success metrics, duration
- experiment_recommendation: Which experiments to run based on analytics
- experiment_result: Collected results and statistical significance
- growth_insight: Actionable insights from completed experiments
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class ExperimentType(Enum):
    """Types of growth experiments per Spec #19."""
    STORY_CONCEPT = auto()
    CHARACTER_THEME = auto()
    HOOK = auto()
    VIDEO_LENGTH = auto()
    TITLE = auto()
    THUMBNAIL = auto()
    POSTING_SCHEDULE = auto()


class ExperimentStatus(Enum):
    """Experiment lifecycle status."""
    DRAFT = auto()
    APPROVED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    CANCELLED = auto()


@dataclass
class ExperimentVariant:
    """A variant in an A/B test experiment."""
    variant_id: str
    name: str
    description: str
    config: dict[str, Any]  # Variant-specific configuration


@dataclass
class ExperimentDesign:
    """Design of a growth experiment."""
    experiment_id: str
    experiment_type: ExperimentType
    hypothesis: str
    variants: list[ExperimentVariant]
    success_metrics: list[str]  # e.g., ["views", "ctr", "retention"]
    min_sample_size: int
    duration_days: int
    status: ExperimentStatus
    created_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class ExperimentResult:
    """Results of a completed experiment."""
    experiment_id: str
    variant_id: str
    metric_name: str
    variant_value: float
    control_value: float
    lift_percentage: float
    is_statistically_significant: bool
    confidence_level: float
    collected_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class GrowthInsight:
    """Actionable insight from completed experiments."""
    insight_id: str
    experiment_id: str
    insight: str
    recommended_action: str
    confidence: str  # "high", "medium", "low"
    applies_to: list[str]  # e.g., ["all_episodes", "lalin_character"]
    created_at: str = field(default_factory=lambda: uuid4().hex[:12])


class GrowthExperimentAgent:
    """Agent 17 -- Growth Experiment Agent implementation."""

    AGENT_ID = "AGENT_17"
    AGENT_NAME = "Growth Experiment Agent"
    DESCRIPTION = "Recommends creative experiments based on actual analytics"

    # Default experiment templates per Spec #19
    EXPERIMENT_TEMPLATES = {
        ExperimentType.STORY_CONCEPT: {
            "hypothesis": "Different story concepts drive different engagement rates",
            "success_metrics": ["views", "average_view_duration", "audience_retention"],
            "min_sample_size": 1000,
            "duration_days": 14,
        },
        ExperimentType.CHARACTER_THEME: {
            "hypothesis": "Character-themed episodes outperform general episodes",
            "success_metrics": ["views", "subscribers_gained", "comments"],
            "min_sample_size": 1000,
            "duration_days": 14,
        },
        ExperimentType.HOOK: {
            "hypothesis": "Stronger 0-3 second hooks improve audience retention",
            "success_metrics": ["audience_retention_percentage", "average_view_duration"],
            "min_sample_size": 500,
            "duration_days": 7,
        },
        ExperimentType.VIDEO_LENGTH: {
            "hypothesis": "Optimal video length varies by content type",
            "success_metrics": ["average_view_duration", "completion_rate"],
            "min_sample_size": 500,
            "duration_days": 14,
        },
        ExperimentType.TITLE: {
            "hypothesis": "Different title styles affect click-through rate",
            "success_metrics": ["ctr", "views"],
            "min_sample_size": 1000,
            "duration_days": 7,
        },
        ExperimentType.THUMBNAIL: {
            "hypothesis": "Thumbnail design affects click-through rate",
            "success_metrics": ["ctr", "views"],
            "min_sample_size": 1000,
            "duration_days": 7,
        },
        ExperimentType.POSTING_SCHEDULE: {
            "hypothesis": "Posting time affects initial view velocity",
            "success_metrics": ["views_first_24h", "subscribers_gained"],
            "min_sample_size": 500,
            "duration_days": 21,
        },
    }

    def __init__(self):
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID
        self._designs: dict[str, ExperimentDesign] = {}
        self._results: dict[str, list[ExperimentResult]] = {}
        self._insights: dict[str, GrowthInsight] = {}

    def design_experiment(
        self, experiment_type: ExperimentType, hypothesis: str,
        variants: list[dict[str, Any]], success_metrics: list[str],
        min_sample_size: int, duration_days: int,
    ) -> ExperimentDesign:
        """Design a new growth experiment."""
        experiment_id = f"exp_{uuid4().hex[:8]}"

        variant_objects = [
            ExperimentVariant(
                variant_id=f"variant_{i}_{uuid4().hex[:6]}",
                name=v.get("name", f"Variant {i+1}"),
                description=v.get("description", ""),
                config=v.get("config", {}),
            )
            for i, v in enumerate(variants)
        ]

        design = ExperimentDesign(
            experiment_id=experiment_id,
            experiment_type=experiment_type,
            hypothesis=hypothesis,
            variants=variant_objects,
            success_metrics=success_metrics,
            min_sample_size=min_sample_size,
            duration_days=duration_days,
            status=ExperimentStatus.DRAFT,
        )
        self._designs[experiment_id] = design
        return design

    def recommend_experiments(
        self, analytics_summary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Recommend experiments based on actual analytics data.

        Per Spec #19: recommendations must be based on actual analytics,
        not manufactured engagement.
        """
        recommendations = []

        # Analyze retention to suggest hook experiments
        avg_retention = analytics_summary.get(
            "average_audience_retention", 50.0
        )
        if avg_retention < 50.0:
            recommendations.append({
                "experiment_type": ExperimentType.HOOK.name,
                "reason": (
                    f"Average audience retention {avg_retention}% is below 50%. "
                    f"Test stronger 0-3 second hooks."
                ),
                "priority": "high",
            })

        # Analyze CTR to suggest title/thumbnail experiments
        avg_ctr = analytics_summary.get("average_ctr", 5.0)
        if avg_ctr < 4.0:
            recommendations.append({
                "experiment_type": ExperimentType.TITLE.name,
                "reason": (
                    f"Average CTR {avg_ctr}% is below 4%. "
                    f"Test different title styles."
                ),
                "priority": "high",
            })
            recommendations.append({
                "experiment_type": ExperimentType.THUMBNAIL.name,
                "reason": (
                    f"Average CTR {avg_ctr}% is below 4%. "
                    f"Test different thumbnail designs."
                ),
                "priority": "high",
            })

        # Always suggest character theme experiment
        recommendations.append({
            "experiment_type": ExperimentType.CHARACTER_THEME.name,
            "reason": (
                "Test which character themes drive the most engagement "
                "across LALIN, NICHA, PIM, YADA."
            ),
            "priority": "medium",
        })

        # Suggest posting schedule experiment
        recommendations.append({
            "experiment_type": ExperimentType.POSTING_SCHEDULE.name,
            "reason": (
                "Test optimal posting times for initial view velocity."
            ),
            "priority": "medium",
        })

        return recommendations

    def record_result(
        self, experiment_id: str, variant_id: str, metric_name: str,
        variant_value: float, control_value: float,
        is_statistically_significant: bool, confidence_level: float,
    ) -> ExperimentResult:
        """Record an experiment result."""
        result = ExperimentResult(
            experiment_id=experiment_id,
            variant_id=variant_id,
            metric_name=metric_name,
            variant_value=variant_value,
            control_value=control_value,
            lift_percentage=(
                ((variant_value - control_value) / control_value * 100)
                if control_value > 0 else 0.0
            ),
            is_statistically_significant=is_statistically_significant,
            confidence_level=confidence_level,
        )
        if experiment_id not in self._results:
            self._results[experiment_id] = []
        self._results[experiment_id].append(result)
        return result

    def generate_insight(
        self, experiment_id: str, insight: str,
        recommended_action: str, confidence: str, applies_to: list[str],
    ) -> GrowthInsight:
        """Generate an actionable insight from experiment results."""
        insight_id = f"insight_{uuid4().hex[:8]}"

        growth_insight = GrowthInsight(
            insight_id=insight_id,
            experiment_id=experiment_id,
            insight=insight,
            recommended_action=recommended_action,
            confidence=confidence,
            applies_to=applies_to,
        )
        self._insights[insight_id] = growth_insight
        return growth_insight

    def get_experiment(self, experiment_id: str) -> dict[str, Any] | None:
        """Get experiment design as dictionary."""
        if experiment_id not in self._designs:
            return None
        design = self._designs[experiment_id]
        return {
            "experiment_id": design.experiment_id,
            "experiment_type": design.experiment_type.name,
            "hypothesis": design.hypothesis,
            "variants": [
                {
                    "variant_id": v.variant_id,
                    "name": v.name,
                    "description": v.description,
                    "config": v.config,
                }
                for v in design.variants
            ],
            "success_metrics": design.success_metrics,
            "min_sample_size": design.min_sample_size,
            "duration_days": design.duration_days,
            "status": design.status.name,
            "created_at": design.created_at,
        }

    def get_results(self, experiment_id: str) -> list[dict[str, Any]]:
        """Get all results for an experiment."""
        results = self._results.get(experiment_id, [])
        return [
            {
                "experiment_id": r.experiment_id,
                "variant_id": r.variant_id,
                "metric_name": r.metric_name,
                "variant_value": r.variant_value,
                "control_value": r.control_value,
                "lift_percentage": r.lift_percentage,
                "is_statistically_significant": r.is_statistically_significant,
                "confidence_level": r.confidence_level,
                "collected_at": r.collected_at,
            }
            for r in results
        ]

    def get_insights(self) -> list[dict[str, Any]]:
        """Get all generated insights."""
        return [
            {
                "insight_id": i.insight_id,
                "experiment_id": i.experiment_id,
                "insight": i.insight,
                "recommended_action": i.recommended_action,
                "confidence": i.confidence,
                "applies_to": i.applies_to,
                "created_at": i.created_at,
            }
            for i in self._insights.values()
        ]

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "capability": "growth_experiment",
            "experiments_designed": len(self._designs),
            "experiments_with_results": len(self._results),
            "insights_generated": len(self._insights),
            "experiment_types": [t.name for t in ExperimentType],
        }


# Module-level agent instance
agent = GrowthExperimentAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a Growth Experiment Agent action.

    Args:
        action: The action to execute
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "design_experiment":
        design = agent_obj.design_experiment(
            experiment_type=ExperimentType[kwargs.get("experiment_type", "HOOK")],
            hypothesis=kwargs.get("hypothesis", ""),
            variants=kwargs.get("variants", []),
            success_metrics=kwargs.get("success_metrics", ["views"]),
            min_sample_size=kwargs.get("min_sample_size", 500),
            duration_days=kwargs.get("duration_days", 7),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "design_experiment",
            "status": "completed",
            "experiment_id": design.experiment_id,
            "experiment_type": design.experiment_type.name,
            "hypothesis": design.hypothesis,
            "num_variants": len(design.variants),
            "success_metrics": design.success_metrics,
            "min_sample_size": design.min_sample_size,
            "duration_days": design.duration_days,
            "experiment_status": design.status.name,
        }

    elif action == "recommend_experiments":
        recommendations = agent_obj.recommend_experiments(
            analytics_summary=kwargs.get("analytics_summary", {}),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "recommend_experiments",
            "status": "completed",
            "recommendations": recommendations,
        }

    elif action == "record_result":
        result = agent_obj.record_result(
            experiment_id=kwargs.get("experiment_id", ""),
            variant_id=kwargs.get("variant_id", ""),
            metric_name=kwargs.get("metric_name", ""),
            variant_value=kwargs.get("variant_value", 0.0),
            control_value=kwargs.get("control_value", 0.0),
            is_statistically_significant=kwargs.get(
                "is_statistically_significant", False
            ),
            confidence_level=kwargs.get("confidence_level", 0.0),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "record_result",
            "status": "completed",
            "experiment_id": result.experiment_id,
            "variant_id": result.variant_id,
            "metric_name": result.metric_name,
            "lift_percentage": result.lift_percentage,
            "is_statistically_significant": result.is_statistically_significant,
            "confidence_level": result.confidence_level,
        }

    elif action == "generate_insight":
        insight = agent_obj.generate_insight(
            experiment_id=kwargs.get("experiment_id", ""),
            insight=kwargs.get("insight", ""),
            recommended_action=kwargs.get("recommended_action", ""),
            confidence=kwargs.get("confidence", "medium"),
            applies_to=kwargs.get("applies_to", []),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "generate_insight",
            "status": "completed",
            "insight_id": insight.insight_id,
            "experiment_id": insight.experiment_id,
            "insight": insight.insight,
            "recommended_action": insight.recommended_action,
            "confidence": insight.confidence,
            "applies_to": insight.applies_to,
        }

    elif action == "get_experiment":
        experiment = agent_obj.get_experiment(kwargs.get("experiment_id", ""))
        if experiment is None:
            return {
                "agent": agent_obj.AGENT_ID,
                "action": "get_experiment",
                "status": "blocked",
                "error": "Experiment not found",
            }
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_experiment",
            "status": "completed",
            "experiment": experiment,
        }

    elif action == "get_results":
        results = agent_obj.get_results(kwargs.get("experiment_id", ""))
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_results",
            "status": "completed",
            "results": results,
        }

    elif action == "get_insights":
        insights = agent_obj.get_insights()
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_insights",
            "status": "completed",
            "insights": insights,
        }

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "GrowthExperimentAgent",
    "ExperimentDesign",
    "ExperimentResult",
    "GrowthInsight",
    "ExperimentVariant",
    "ExperimentType",
    "ExperimentStatus",
    "execute_action",
    "agent",
]