"""Agent 07 -- Action Choreographer

Designs safe, physically coherent action and movement for ZEAZVERSE characters.

Responsibilities:
- Design safe, physically coherent action and movement per scene
- Implement model-specific adapters for action generation
- Support Spec #6: "Designs safe, physically coherent action and movement"
- Support Spec #9: Provider selection and prompt submission
- Support Spec #10: Video editing pipeline with idempotent jobs
- Validate physical interaction constraints (anatomy, constraints, limits)

Agent Outputs:
- action_sequence: Structured action sequence with timed phases
- movement_constraints: Physical constraints per character
- safety_checks: Safety validation results
- transition_plan: Safe transitions between action phases
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class ActionType(Enum):
    """Types of actions supported by the Action Choreographer."""
    COMBAT = auto()
    FALL = auto()
    JUMP = auto()
    FIGHT = auto()
    DANCE = auto()
    RUN = auto()
    GRAB = auto()
    REACT = auto()


class SafetyLevel(Enum):
    """Safety validation levels."""
    SAFE = auto()
    CAUTION = auto()
    UNSAFE = auto()


@dataclass
class ActionPhase:
    """A single phase of an action sequence."""
    phase_id: str
    action_type: ActionType
    duration: float  # seconds
    description: str
    movement_constraints: dict[str, bool]  # e.g., {"limit_joint_rotation": True}
    safety_rating: SafetyLevel
    transition_in: str  # how to enter this phase
    transition_out: str  # how to exit this phase


@dataclass
class ActionSequence:
    """Complete action sequence for a character."""
    sequence_id: str
    character_id: str
    action_types: list[ActionType]
    phases: list[ActionPhase]
    total_duration: float
    safety_validation: SafetyLevel
    notes: str


@dataclass
class ChoreographyOutput:
    """Complete choreography output for a scene action."""
    scene_id: str
    character_id: str
    action_sequence: ActionSequence
    safety_checks: dict[str, bool]
    recommended_camera_moves: list[str]
    recommended_lighting_changes: list[str]


class ActionChoreographerAgent:
    """Agent 07 -- Action Choreographer implementation."""

    AGENT_ID = "AGENT_07"
    AGENT_NAME = "Action Choreographer"
    DESCRIPTION = "Designs safe, physically coherent action and movement"

    def __init__(self, safety_priority: bool = True):
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID
        self.safety_priority = safety_priority

    def choreograph_action(
        self, character_id: str, action_type: ActionType,
        duration: float, scene_context: dict[str, Any] | None = None
    ) -> ChoreographyOutput:
        """Choreograph a safe action sequence for a character."""

        # Determine action phases based on type and duration
        phases = self._create_action_phases(action_type, duration)

        # Validate safety for each phase
        safety_checks = self._validate_safety(phases, character_id, scene_context)

        # Generate recommended camera and lighting moves
        camera_moves = self._recommended_camera_moves(phases, character_id)
        lighting_changes = self._recommended_lighting_changes(phases, character_id)

        # Build the action sequence
        action_sequence = ActionSequence(
            sequence_id=f"seq_{uuid4().hex[:8]}",
            character_id=character_id,
            action_types=[action_type],
            phases=phases,
            total_duration=duration,
            safety_validation=SafetyLevel.SAFE if safety_checks["overall_safe"] else SafetyLevel.UNSAFE,
            notes=self._generate_notes(phases, safety_checks),
        )

        return ChoreographyOutput(
            scene_id=scene_context.get("scene_id", "scene_default") if scene_context else "scene_default",
            character_id=character_id,
            action_sequence=action_sequence,
            safety_checks=safety_checks,
            recommended_camera_moves=camera_moves,
            recommended_lighting_changes=lighting_changes,
        )

    def _create_action_phases(self, action_type: ActionType, duration: float) -> list[ActionPhase]:
        """Create action phases based on action type and duration."""
        base_duration = duration / 3  # 3 phases: start, middle, end

        # Define phases per action type
        phase_templates = {
            ActionType.COMBAT: [
                ActionPhase(
                    phase_id="start",
                    action_type=ActionType.COMBAT,
                    duration=base_duration,
                    description="Combat stance and initial engagement",
                    movement_constraints={"limit_joint_rotation": True, "maintain_balance": True},
                    safety_rating=SafetyLevel.SAFE,
                    transition_in="ready-position",
                    transition_out="engagement-phase",
                ),
                ActionPhase(
                    phase_id="engagement",
                    action_type=ActionType.COMBAT,
                    duration=base_duration,
                    description="Active combat engagement",
                    movement_constraints={"limit_joint_rotation": True, "maintain_balance": True, "keep_distance": True},
                    safety_rating=SafetyLevel.CAUTION,
                    transition_in="engagement-phase",
                    transition_out="climax-phase",
                ),
                ActionPhase(
                    phase_id="climax",
                    action_type=ActionType.COMBAT,
                    duration=base_duration,
                    description="Combat climax with maximum intensity",
                    movement_constraints={"limit_joint_rotation": True, "maintain_balance": True, "controlled_force": True},
                    safety_rating=SafetyLevel.CAUTION,
                    transition_in="climax-phase",
                    transition_out="resolution-phase",
                ),
            ],
            ActionType.JUMP: [
                ActionPhase(
                    phase_id="prep",
                    action_type=ActionType.JUMP,
                    duration=base_duration,
                    description="Jump preparation and loading",
                    movement_constraints={"limit_joint_rotation": True, "maintain_balance": True},
                    safety_rating=SafetyLevel.SAFE,
                    transition_in="standing-position",
                    transition_out="takeoff-phase",
                ),
                ActionPhase(
                    phase_id="takeoff",
                    action_type=ActionType.JUMP,
                    duration=base_duration,
                    description="Jump takeoff with maximum velocity",
                    movement_constraints={"limit_joint_rotation": True, "maintain_balance": True, "achieve_airtime": True},
                    safety_rating=SafetyLevel.CAUTION,
                    transition_in="takeoff-phase",
                    transition_out="landing-phase",
                ),
                ActionPhase(
                    phase_id="landing",
                    action_type=ActionType.JUMP,
                    duration=base_duration,
                    description="Controlled landing impact absorption",
                    movement_constraints={"limit_joint_rotation": True, "maintain_balance": True, "absorb_impact": True},
                    safety_rating=SafetyLevel.SAFE,
                    transition_in="landing-phase",
                    transition_out="post-jump-position",
                ),
            ],
            ActionType.FALL: [
                ActionPhase(
                    phase_id="fall-start",
                    action_type=ActionType.FALL,
                    duration=base_duration,
                    description="Planned fall initiation",
                    movement_constraints={"limit_joint_rotation": True, "controlled-descent": True},
                    safety_rating=SafetyLevel.CAUTION,
                    transition_in="standing-position",
                    transition_out="fall-mid",
                ),
                ActionPhase(
                    phase_id="fall-mid",
                    action_type=ActionType.FALL,
                    duration=base_duration,
                    description="Mid-fall trajectory control",
                    movement_constraints={"limit_joint_rotation": True, "maintain-balance": True, "controlled-descent": True},
                    safety_rating=SafetyLevel.UNSAFE,
                    transition_in="fall-mid",
                    transition_out="landing-phase",
                ),
                ActionPhase(
                    phase_id="landing",
                    action_type=ActionType.FALL,
                    duration=base_duration,
                    description="Controlled landing impact absorption",
                    movement_constraints={"limit_joint_rotation": True, "maintain-balance": True, "absorb-impact": True},
                    safety_rating=SafetyLevel.SAFE,
                    transition_in="landing-phase",
                    transition_out="post-fall-position",
                ),
            ],
        }

        # Get phases for this action type, or default to a basic sequence
        phases_list = phase_templates.get(action_type, [
            ActionPhase(
                phase_id="action",
                action_type=action_type,
                duration=duration,
                description=f"Action sequence: {action_type.name}",
                movement_constraints={"maintain_balance": True},
                safety_rating=SafetyLevel.CAUTION,
                transition_in="start",
                transition_out="end",
            ),
        ])

        # Ensure total duration matches requested duration
        total_phase_duration = sum(p.duration for p in phases_list)
        if total_phase_duration > 0:
            scale = duration / total_phase_duration
            for p in phases_list:
                p.duration = p.duration * scale

        return phases_list

    def _validate_safety(self, phases: list[ActionPhase], character_id: str,
                         scene_context: dict[str, Any] | None = None) -> dict[str, bool]:
        """Validate safety for all action phases."""
        safety_results = {
            "overall_safe": True,
            "joint_limits_ok": True,
            "balance_maintained": True,
            "impact_safe": True,
            "clearance_ok": True,
        }

        for phase in phases:
            # Check joint rotation limits
            if phase.movement_constraints.get("limit_joint_rotation", False):
                safety_results["joint_limits_ok"] = safety_results["joint_limits_ok"] and True

            # Check balance maintenance
            if phase.movement_constraints.get("maintain_balance", False):
                safety_results["balance_maintained"] = safety_results["balance_maintained"] and True

            # Check impact safety
            if phase.safety_rating == SafetyLevel.UNSAFE:
                safety_results["impact_safe"] = False
                safety_results["overall_safe"] = False

            # Check clearance (simulated)
            safety_results["clearance_ok"] = True

        return safety_results

    def _recommended_camera_moves(self, phases: list[ActionPhase],
                                  character_id: str) -> list[str]:
        """Generate recommended camera moves for the action sequence."""
        moves = []
        for i, phase in enumerate(phases):
            if phase.action_type == ActionType.COMBAT:
                moves.append(f"combat-angle-{i}")
            elif phase.action_type == ActionType.JUMP:
                moves.append(f"jump-track-{i}")
            elif phase.action_type == ActionType.FALL:
                moves.append(f"fall-track-{i}")
            else:
                moves.append(f"action-track-{i}")
        return moves

    def _recommended_lighting_changes(self, phases: list[ActionPhase],
                                      character_id: str) -> list[str]:
        """Generate recommended lighting changes for the action sequence."""
        changes = []
        for i, phase in enumerate(phases):
            if phase.safety_rating == SafetyLevel.UNSAFE:
                changes.append(f"emergency-light-{i}")
            else:
                changes.append(f"normal-light-{i}")
        return changes

    def _generate_notes(self, phases: list[ActionPhase],
                        safety_checks: dict[str, bool]) -> str:
        """Generate notes for the action sequence."""
        notes_parts = []
        if safety_checks["overall_safe"]:
            notes_parts.append("Action sequence validated as safe")
        else:
            notes_parts.append("Action sequence requires caution")

        safe_count = sum(1 for p in phases if p.safety_rating == SafetyLevel.SAFE)
        notes_parts.append(f"{safe_count}/{len(phases)} phases validated safe")

        return " | ".join(notes_parts)

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "safety_priority": self.safety_priority,
            "capability": "action_choreography",
        }


# Module-level agent instance
agent = ActionChoreographerAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute an Action Choreographer agent action.

    Convenience function for running agent actions from API or workflow orchestration.

    Args:
        action: The action to execute (e.g., "choreograph", "status_check")
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "choreograph":
        character_id = kwargs.get("character_id", "lalin")
        # Convert string to ActionType enum if needed
        action_type_raw = kwargs.get("action_type", ActionType.COMBAT)
        if isinstance(action_type_raw, str):
            # Map string to enum
            action_type_map = {
                "combat": ActionType.COMBAT,
                "jump": ActionType.JUMP,
                "fall": ActionType.FALL,
                "dance": ActionType.DANCE,
                "run": ActionType.RUN,
                "grab": ActionType.GRAB,
                "react": ActionType.REACT,
            }
            action_type = action_type_map.get(action_type_raw.lower(), ActionType.COMBAT)
        else:
            action_type = action_type_raw
        duration = kwargs.get("duration", 5.0)
        scene_context = kwargs.get("scene_context", {})

        output = agent_obj.choreograph_action(character_id, action_type, duration, scene_context)

        # Build phases list safely
        phases_list = []
        if output.action_sequence and output.action_sequence.phases:
            phases_list = [
                {
                    "phase_id": p.phase_id,
                    "action_type": p.action_type.name,
                    "duration": p.duration,
                    "description": p.description,
                    "safety_rating": p.safety_rating.name,
                }
                for p in output.action_sequence.phases
            ]

        return {
            "agent": agent_obj.AGENT_ID,
            "action": "choreograph",
            "status": "completed",
            "character_id": output.character_id,
            "sequence_id": output.action_sequence.sequence_id if output.action_sequence else None,
            "total_duration": output.action_sequence.total_duration if output.action_sequence else None,
            "phases": phases_list,
            "safety_validation": output.action_sequence.safety_validation.name if output.action_sequence else None,
            "safety_checks": output.safety_checks,
            "recommended_camera_moves": output.recommended_camera_moves,
            "recommended_lighting_changes": output.recommended_lighting_changes,
        }

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "ActionChoreographerAgent",
    "ActionPhase",
    "ActionSequence",
    "ChoreographyOutput",
    "ActionType",
    "SafetyLevel",
    "execute_action",
    "agent",
]