"""Agent 14 -- Policy & Rights Agent

Checks AI disclosure requirements, content rights, metadata accuracy 
and platform restrictions per Spec #14 and #16.

Responsibilities:
- Validate AI disclosure compliance per YouTube policies
- Check content rights and metadata accuracy
- Validate platform restrictions and limitations
- Enforce human approval for high-impact actions
- Generate evidence for audit trail

Agent Outputs:
- compliance_status: PASS/FAIL/REVIEW
- disclosure_check: results of AI disclosure validation
- rights_check: content rights status
- metadata_accuracy: validation results
- platform_restrictions: applicable restrictions
- evidence: supporting documentation
- required_actions: list of remediation steps needed
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class ComplianceStatus(Enum):
    """Compliance evaluation status."""
    PASS = auto()
    FAIL = auto()
    REVIEW = auto()


class RightsStatus(Enum):
    """Content rights evaluation status."""
    CLEAR = auto()
    PENDING_REVIEW = auto()
    RESTRICTED = auto()
    BLOCKED = auto()


class RestrictionType(Enum):
    """Types of platform restrictions."""
    AGE_RESTRICTED = auto()
    COMMUNITY_GUIDELINE = auto()
    COPYRIGHT = auto()
    ADVERTISER_FRIENDLY = auto()
    AI_DISCLOSURE = auto()


@dataclass
class PolicyCheckResult:
    """Result of a policy & rights check."""
    episode_id: str
    compliance_status: ComplianceStatus
    rights_status: RightsStatus
    disclosure_check: dict[str, Any]
    metadata_accuracy: dict[str, Any]
    platform_restrictions: list[RestrictionType]
    evidence: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)
    checked_at: str = field(default_factory=lambda: uuid4().hex[:12])


class PolicyRightsAgent:
    """Agent 14 -- Policy & Rights Agent implementation."""

    AGENT_ID = "AGENT_14"
    AGENT_NAME = "Policy & Rights Agent"
    DESCRIPTION = "Checks AI disclosure requirements, content rights, metadata accuracy and platform restrictions"

    def __init__(self):
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID

    def check_policy_rights(
        self, episode_id: str, series_id: str,
        character_ids: list[str],
        theme: str,
        content_type: str,
        metadata: dict[str, Any],
    ) -> PolicyCheckResult:
        """Complete policy and rights check for an episode."""

        # Check AI disclosure compliance
        disclosure_check = self._check_disclosure_compliance(
            content_type, metadata
        )

        # Check content rights
        rights_check = self._check_content_rights(
            theme, character_ids, metadata
        )

        # Validate metadata accuracy
        metadata_accuracy = self._validate_metadata_accuracy(metadata)

        # Determine platform restrictions
        platform_restrictions = self._determine_platform_restrictions(
            theme, content_type, disclosure_check, rights_check
        )

        # Calculate overall compliance
        compliance_status = self._calculate_compliance(
            disclosure_check, rights_check, platform_restrictions
        )

        # Generate required actions
        required_actions = self._generate_required_actions(
            compliance_status, platform_restrictions, disclosure_check, rights_check
        )

        return PolicyCheckResult(
            episode_id=episode_id,
            compliance_status=compliance_status,
            rights_status=rights_check,
            disclosure_check=disclosure_check,
            metadata_accuracy=metadata_accuracy,
            platform_restrictions=platform_restrictions,
            evidence=[f"Checked {episode_id} per Spec #14 & #16"],
            required_actions=required_actions,
            checked_at=uuid4().hex[:12],
        )

    def _check_disclosure_compliance(
        self, content_type: str, metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Check AI disclosure compliance per YouTube policies."""
        has_ai_content = content_type in [
            "cinematic_action", "fantasy_adventures", "cyberpunk_stories"
        ]

        # Check if disclosure is already present in metadata
        existing_disclosure = metadata.get("disclosure_metadata", {})

        if has_ai_content:
            # AI-generated content requires disclosure
            disclosure_type = existing_disclosure.get(
                "has_ai_generated_content", False
            )

            if disclosure_type:
                # Disclosure present and accurate
                return {
                    "compliant": True,
                    "disclosure_type": "AI_GENERATED",
                    "disclosure_text": existing_disclosure.get(
                        "disclosure_text", "This video features AI-generated virtual characters."
                    ),
                    "status": "PASS",
                    "required_disclosure": True,
                }
            else:
                # Missing disclosure for AI content
                return {
                    "compliant": False,
                    "disclosure_type": None,
                    "disclosure_text": None,
                    "status": "FAIL",
                    "required_disclosure": True,
                    "missing_info": "AI content present but no AI disclosure metadata found",
                }
        else:
            # No AI content - disclosure may still be appropriate
            return {
                "compliant": True,
                "disclosure_type": "NONE",
                "disclosure_text": existing_disclosure.get(
                    "disclosure_text", "No AI-generated content detected."
                ),
                "status": "PASS",
                "required_disclosure": False,
            }

    def _check_content_rights(
        self, theme: str, character_ids: list[str],
        metadata: dict[str, Any],
    ) -> RightsStatus:
        """Check content rights and metadata accuracy."""
        # Check for restricted themes
        restricted_themes = ["comedy_shorts"]  # Could add more based on policy

        # Check character usage - all characters should be original/authorized
        unauthorized_chars = []
        for cid in character_ids:
            if cid.upper() not in ["LALIN", "NICHA", "PIM", "YADA"]:
                unauthorized_chars.append(cid)

        if unauthorized_chars:
            return RightsStatus.BLOCKED

        # Check theme for rights concerns
        if theme in restricted_themes:
            return RightsStatus.PENDING_REVIEW

        # Check metadata for proper attribution
        has_proper_attribution = (
            metadata.get("has_ai_generated_content", False)
            or metadata.get("no_ai_content", True)
        )

        if not has_proper_attribution:
            return RightsStatus.PENDING_REVIEW

        return RightsStatus.CLEAR

    def _validate_metadata_accuracy(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Validate metadata accuracy."""
        errors = []
        warnings = []

        # Check title/description
        title = metadata.get("primary_description", "")
        if not title or len(title) < 10:
            errors.append("Primary description too short or missing")

        # Check description
        description = metadata.get("primary_description", "")
        if not description:
            errors.append("Primary description missing")

        # Check keywords
        keywords = metadata.get("search_keywords", [])
        if not keywords:
            warnings.append("No search keywords provided")

        # Check hashtags
        hashtags = metadata.get("appropriate_hashtags", [])
        if len(hashtags) < 3:
            warnings.append("Few hashtags provided - may reduce discoverability")

        # Check disclosure
        disclosure = metadata.get("disclosure_metadata", {})
        if disclosure.get("has_ai_generated_content", False) and not disclosure.get("disclosure_text"):
            errors.append("AI content detected but disclosure text missing")

        accuracy = {
            "errors": errors,
            "warnings": warnings,
            "is_valid": len(errors) == 0,
        }

        return accuracy

    def _determine_platform_restrictions(
        self, theme: str, content_type: str,
        disclosure_check: dict[str, Any],
        rights_check: RightsStatus,
    ) -> list[RestrictionType]:
        """Determine applicable platform restrictions."""
        restrictions = []

        # AI disclosure restrictions
        if not disclosure_check.get("compliant", False):
            restrictions.append(RestrictionType.AI_DISCLOSURE)

        # Content-specific restrictions
        if content_type == "cinematic_action":
            # Action content may have age/restriction concerns
            if not disclosure_check.get("compliant", False):
                restrictions.append(RestrictionType.COMMUNITY_GUIDELINE)

        # Rights-based restrictions
        if rights_check in [RightsStatus.PENDING_REVIEW, RightsStatus.BLOCKED]:
            restrictions.append(RestrictionType.COPYRIGHT)

        # Default: at minimum, check AI disclosure
        if not restrictions:
            if not disclosure_check.get("compliant", False):
                restrictions.append(RestrictionType.AI_DISCLOSURE)

        return restrictions

    def _calculate_compliance(
        self, disclosure_check: dict[str, Any],
        rights_check: RightsStatus,
        platform_restrictions: list[RestrictionType],
    ) -> ComplianceStatus:
        """Calculate overall compliance status."""

        # If any critical failure
        if not disclosure_check.get("compliant", False):
            return ComplianceStatus.FAIL

        if rights_check in [RightsStatus.PENDING_REVIEW, RightsStatus.BLOCKED]:
            return ComplianceStatus.FAIL

        if RestrictionType.AI_DISCLOSURE in platform_restrictions:
            return ComplianceStatus.FAIL

        if RestrictionType.COPYRIGHT in platform_restrictions:
            return ComplianceStatus.FAIL

        # If there are pending reviews
        if RestrictionType.COMMUNITY_GUIDELINE in platform_restrictions:
            return ComplianceStatus.REVIEW

        return ComplianceStatus.PASS

    def _generate_required_actions(
        self, compliance_status: ComplianceStatus,
        platform_restrictions: list[RestrictionType],
        disclosure_check: dict[str, Any],
        rights_check: RightsStatus,
    ) -> list[str]:
        """Generate required remediation actions."""
        actions = []

        if compliance_status == ComplianceStatus.FAIL:
            if not disclosure_check.get("compliant", False):
                actions.append(
                    "Add AI disclosure metadata to episode metadata"
                )
            if rights_check in [RightsStatus.PENDING_REVIEW, RightsStatus.BLOCKED]:
                actions.append(
                    "Review and resolve content rights issues"
                )
            if RestrictionType.COPYRIGHT in platform_restrictions:
                actions.append(
                    "Verify all assets are properly licensed or original"
                )
            if RestrictionType.AI_DISCLOSURE in platform_restrictions:
                actions.append(
                    "Ensure AI disclosure is present and accurate"
                )

        elif compliance_status == ComplianceStatus.REVIEW:
            if RestrictionType.COMMUNITY_GUIDELINE in platform_restrictions:
                actions.append(
                    "Review content against community guidelines"
                )

        elif compliance_status == ComplianceStatus.PASS:
            # Even passing checks may have optional improvements
            if not disclosure_check.get("compliant", False) and disclosure_check.get(
                "required_disclosure", False
            ):
                actions.append(
                    "Consider adding AI disclosure for transparency"
                )

        return actions

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "capability": "policy_rights",
        }


# Module-level agent instance
agent = PolicyRightsAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a Policy & Rights Agent agent action.

    Convenience function for running agent actions from API or workflow orchestration.

    Args:
        action: The action to execute (e.g., "check_policy_rights", "status_check")
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "check_policy_rights":
        episode_id = kwargs.get("episode_id", f"episode_{uuid4().hex[:6]}")
        series_id = kwargs.get("series_id", "series_default")
        character_ids = kwargs.get("character_ids", ["lalin"])
        theme = kwargs.get("theme", "original_story")
        content_type = kwargs.get("content_type", "original_story")
        metadata = kwargs.get("metadata", {})

        result = agent_obj.check_policy_rights(
            episode_id=episode_id,
            series_id=series_id,
            character_ids=character_ids,
            theme=theme,
            content_type=content_type,
            metadata=metadata,
        )

        return {
            "agent": agent_obj.AGENT_ID,
            "action": "check_policy_rights",
            "status": "completed",
            "episode_id": result.episode_id,
            "series_id": series_id,
            "compliance_status": result.compliance_status.name,
            "rights_status": result.rights_status.name,
            "disclosure_check": result.disclosure_check,
            "metadata_accuracy": result.metadata_accuracy,
            "platform_restrictions": [r.name for r in result.platform_restrictions],
            "evidence": result.evidence,
            "required_actions": result.required_actions,
            "checked_at": result.checked_at,
        }

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "PolicyRightsAgent",
    "PolicyCheckResult",
    "ComplianceStatus",
    "RightsStatus",
    "RestrictionType",
    "execute_action",
    "agent",
]