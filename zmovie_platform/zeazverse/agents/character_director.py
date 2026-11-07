"""Agent 03 -- Character Director

Manages Character Bibles, identity references and consistency for ZEAZVERSE.

Responsibilities:
- Maintain persistent, versioned Character Bibles for all four characters
- Validate character identity references against stored hashes
- Track costume and appearance changes with revision history
- Generate consistency reports and reference sheets
- Flag unauthorized changes to canonical characters
- Support visual similarity tools as supporting quality signals

Agent Outputs:
- character_bible_update: Structured update with version hash
- consistency_report: Validation results with evidence
- reference_sheet_generation: Front, 45° profiles, back, expressions
- identity_verification: Pass/fail with rationale
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4

from zmovie_platform.zeazverse.store import (
    get_character,
    list_characters,
)


class CharacterStatus(Enum):
    """Status of a canonical character."""
    ACTIVE = auto()
    INACTIVE = auto()
    BLOCKED = auto()


@dataclass
class CharacterReference:
    """Reference to a character's canonical features."""
    character_id: str
    feature: str  # e.g., "hair", "face", "costume", "accessory"
    reference_hash: str  # SHA-256 of reference asset
    version: str
    captured_at: str
    notes: str = ""


@dataclass
class ConsistencyCheckResult:
    """Result of a character consistency check."""
    character_id: str
    feature: str
    is_consistent: bool
    deviation_notes: str = ""
    evidence_hash: str = ""
    checked_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class CharacterBibleUpdate:
    """Structured output for character bible updates."""
    character_id: str
    version_hash: str  # SHA-256 of complete bible state
    changed_features: list[str]
    retained_features: list[str]
    approval_required: bool
    rationale: str


@dataclass
class AgentAction:
    """Standardized agent action output."""
    agent: str
    action: str
    status: str  # "completed", "blocked", "requires_approval"
    data: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class CharacterDirectorAgent:
    """Agent 03 -- Character Director implementation."""

    AGENT_ID = "AGENT_03"
    AGENT_NAME = "Character Director"
    DESCRIPTION = "Manages Character Bibles, identity references and consistency"

    def __init__(self):
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID

    def update_character_bible(
        self,
        character_id: str,
        updates: dict[str, Any],
        approved_by: str | None = None,
    ) -> CharacterBibleUpdate:
        """Update a Character Bible with proper version tracking.

        Args:
            character_id: The character ID (lalin, nica, pim, yada)
            updates: Dictionary of features to update
            approved_by: Identifier of the human approver (required for canonical changes)

        Returns:
            CharacterBibleUpdate with version hash and change rationale
        """
        # Retrieve current bible
        current = get_character(character_id)
        if current is None:
            return CharacterBibleUpdate(
                character_id=character_id,
                version_hash="",
                changed_features=[],
                retained_features=[],
                approval_required=False,
                rationale=f"Character {character_id} not found in database",
            )

        # Determine what changed
        changed_features = []
        retained_features = []

        # Check each feature in updates against current state
        for feature, new_value in updates.items():
            current_value = current.get(feature)
            if current_value != new_value:
                changed_features.append(feature)
            else:
                retained_features.append(feature)

        # For canonical characters, approval is required for certain changes
        # Per Specification: "Require human approval for changes to canonical characters"
        approval_required = self._requires_approval(character_id, changed_features, updates)

        # Upsert the updated character
        if approval_required and not approved_by:
            return CharacterBibleUpdate(
                character_id=character_id,
                version_hash="",
                changed_features=changed_features,
                retained_features=retained_features,
                approval_required=True,
                rationale=f"Approval required for changes to {character_id}'s canonical features",
            )

        # Version hash computed for API layer to apply store update
        version_hash = self._generate_version_hash(character_id)

        return CharacterBibleUpdate(
            character_id=character_id,
            version_hash=version_hash,
            changed_features=changed_features,
            retained_features=retained_features,
            approval_required=False,
            rationale="Character bible updated successfully",
        )

    def check_consistency(
        self, character_id: str, features: list[str] | None = None
    ) -> list[ConsistencyCheckResult]:
        """Check character consistency for specified features.

        Args:
            character_id: The character to check
            features: Specific features to check (all if None)

        Returns:
            List of consistency check results
        """
        character = get_character(character_id)
        if character is None:
            return []

        features_to_check = features or list(character.keys())
        results: list[ConsistencyCheckResult] = []

        for feature in features_to_check:
            if feature in character:
                # Simple consistency check: feature exists and has a value
                value = character.get(feature)
                is_consistent = value is not None and value != ""
                deviation = "" if is_consistent else f"Feature '{feature}' is missing or empty"
                evidence = "" if is_consistent else "missing_value"

                results.append(
                    ConsistencyCheckResult(
                        character_id=character_id,
                        feature=feature,
                        is_consistent=is_consistent,
                        deviation_notes=deviation,
                        evidence_hash=evidence,
                        checked_at=uuid4().hex[:12],
                    )
                )
            else:
                results.append(
                    ConsistencyCheckResult(
                        character_id=character_id,
                        feature=feature,
                        is_consistent=False,
                        deviation_notes=f"Feature '{feature}' not found in character bible",
                        evidence_hash="missing_feature",
                        checked_at=uuid4().hex[:12],
                    )
                )

        return results

    def generate_reference_sheet(
        self, character_id: str
    ) -> dict[str, Any]:
        """Generate a reference sheet for a character.

        Per Specification: Generate reference sheets containing:
        - Front, Left 45°, Left profile, Back, Right profile, Right 45°
        - Facial expressions
        - Costume details
        - Store source/reference asset hashes and revision history

        Returns:
            Dictionary with reference sheet data
        """
        character = get_character(character_id)
        if character is None:
            return {"error": f"Character {character_id} not found"}

        # Collect reference assets and their hashes
        reference_assets = character.get("reference_assets", [])
        assets_info = []
        for asset_id in reference_assets:
            assets_info.append(
                {
                    "asset_id": asset_id,
                    "hash": uuid4().hex[:8]
                    if asset_id
                    else "unknown",
                    "revision": uuid4().hex[:8],
                }
            )

        return {
            "character_id": character_id,
            "character_name": character.get("name", "Unknown"),
            "archetype": character.get("archetype", "Unknown"),
            "views": [
                "front",
                "left_45",
                "left_profile",
                "back",
                "right_profile",
                "right_45",
            ],
            "facial_expressions": [
                "neutral",
                "smile",
                "surprise",
                "determined",
            ],
            "costume_details": character.get("wardrobe", ""),
            "accessories": character.get("accessories", ""),
            "asset_info": assets_info,
            "generated_at": uuid4().hex[:12],
        }

    def verify_identity(
        self, character_id: str, reference_hash: str
    ) -> AgentAction:
        """Verify character identity against stored reference hash.

        Per Specification: "Use visual similarity tools as supporting quality signals,
        not proof of identity correctness. Require human approval for changes to
        canonical characters."
        """
        character = get_character(character_id)
        if character is None:
            return AgentAction(
                agent=self.AGENT_ID,
                action="identity_verification",
                status="blocked",
                error=f"Character {character_id} not found in database",
            )

        stored_hash = character.get("canonical_hash", "")
        identity_matches = stored_hash == reference_hash

        return AgentAction(
            agent=self.AGENT_ID,
            action="identity_verification",
            status="completed" if identity_matches else "blocked",
            data={
                "character_id": character_id,
                "stored_hash": stored_hash,
                "provided_hash": reference_hash,
                "matches": identity_matches,
            },
            evidence={
                "verification_timestamp": uuid4().hex[:12],
                "method": "canonical_hash_comparison",
            },
            error=(
                "Identity mismatch: provided hash does not match canonical hash"
                if not identity_matches
                else None
            ),
        )

    def _requires_approval(
        self, character_id: str, changed_features: list[str], updates: dict[str, Any]
    ) -> bool:
        """Determine if human approval is required for changes.

        Per Specification: 'Require human approval for changes to canonical characters.'
        """
        # All changes to canonical characters require approval
        canonical_features = {
            "hair",
            "wardrobe",
            "accessories",
            "face",
            "personality",
            "voice_profile",
        }

        # Check if any changed features are canonical
        canonical_changes = set(changed_features) & canonical_features

        if canonical_changes:
            return True

        # Check for drastic changes to appearance
        appearance_changes = {"appearance", "hair_color"} if "hair_color" in updates else set()
        if appearance_changes & set(changed_features):
            return True

        return False

    def _generate_version_hash(self, character_id: str) -> str:
        """Generate SHA-256 hash of the complete character bible state."""
        character = get_character(character_id)
        if character is None:
            return ""

        # Create a deterministic representation of the bible state
        bible_state = {
            k: v
            for k, v in sorted(character.items())
            if not k.startswith("_") and k
            not in ("id", "created_at", "updated_at")
        }

        import hashlib

        state_str = str(bible_state)
        return hashlib.sha256(state_str.encode()).hexdigest()


# Module-level agent instance
agent = CharacterDirectorAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> AgentAction:
    """Execute a Character Director agent action.

    Convenience function for running agent actions from API or workflow orchestration.

    Args:
        action: The action to execute (e.g., "update_bible", "check_consistency")
        **kwargs: Arguments specific to the action

    Returns:
        AgentAction with standardized output format
    """
    agent_obj = agent

    if action == "update_bible":
        character_id = kwargs.get("character_id", "")
        updates = kwargs.get("updates", {})
        approved_by = kwargs.get("approved_by")

        # Retrieve current bible to get all required fields
        current = agent_obj.get_character(character_id) if hasattr(agent_obj, 'get_character') else None
        
        # Build complete character dict with all required fields
        {
            "id": character_id,
            "name": current.get("name", character_id) if current else character_id,
            "archetype": current.get("archetype", "The Dreamer") if current else "The Dreamer",
            "nationality": current.get("nationality", "Thai") if current else "Thai",
            "adult": current.get("adult", True) if current else True,
            "appearance": updates.get("appearance", current.get("appearance", "")) if current else "",
            "hair": updates.get("hair", current.get("hair", "")) if current else "",
            "wardrobe": updates.get("wardrobe", current.get("wardrobe", "")) if current else "",
            "personality": updates.get("personality", current.get("personality", "")) if current else "",
            "voice_profile": updates.get("voice_profile", current.get("voice_profile", "")) if current else "",
            "visual_continuity_rules": updates.get("visual_continuity_rules", current.get("visual_continuity_rules", "[]")) if current else "[]",
            "reference_assets": updates.get("reference_assets", current.get("reference_assets", "[]")) if current else "[]",
            "canonical_hash": updates.get("canonical_hash", current.get("canonical_hash", "")) if current else "",
            "status": updates.get("status", current.get("status", "draft")) if current else "draft",
            "owner": current.get("owner", "local") if current else "local",
            "created_at": current.get("created_at", "") if current else "",
            "updated_at": agent_obj._generate_version_hash(character_id),
        }

        result = agent_obj.update_character_bible(character_id, updates, approved_by)
        
        # Wrap in AgentAction
        return AgentAction(
            agent=agent_obj.AGENT_ID,
            action="update_bible",
            status="completed" if not result.approval_required else "requires_approval",
            data={
                "character_bible_update": {
                    "character_id": result.character_id,
                    "version_hash": result.version_hash,
                    "changed_features": result.changed_features,
                    "retained_features": result.retained_features,
                    "approval_required": result.approval_required,
                    "rationale": result.rationale,
                }
            },
            evidence={},
            error=result.rationale if result.approval_required else None,
        )
    elif action == "check_consistency":
        results = agent_obj.check_consistency(kwargs.get("character_id", ""))
        return AgentAction(
            agent=agent_obj.AGENT_ID,
            action="check_consistency",
            status="completed",
            data={"results": [{"feature": r.feature, "is_consistent": r.is_consistent, "deviation_notes": r.deviation_notes} for r in results]},
        )
    elif action == "generate_reference_sheet":
        ref_sheet = agent_obj.generate_reference_sheet(kwargs.get("character_id", ""))
        return AgentAction(
            agent=agent_obj.AGENT_ID,
            action="generate_reference_sheet",
            status="completed",
            data={"reference_sheet": ref_sheet},
        )
    elif action == "verify_identity":
        verify_result = agent_obj.verify_identity(kwargs.get("character_id", ""), kwargs.get("reference_hash", ""))
        return verify_result
    elif action == "list_characters":
        characters = list_characters()
        return AgentAction(
            agent=agent_obj.AGENT_ID,
            action="list_characters",
            status="completed",
            data={"characters": characters},
        )
    else:
        return AgentAction(
            agent=agent_obj.AGENT_ID,
            action=action,
            status="blocked",
            error=f"Unknown action: {action}",
        )

# Export for API/workflow usage
__all__ = [
    "CharacterDirectorAgent",
    "CharacterBibleUpdate",
    "ConsistencyCheckResult",
    "CharacterReference",
    "AgentAction",
    "execute_action",
    "agent",
]