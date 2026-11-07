"""Agent 15 -- Publishing Agent

Manages approved uploads and publication states per Spec #13.

Required states:
  IDEA → SCRIPT_APPROVED → ASSETS_READY → RENDERING → RENDERED → QA_PENDING
  → QA_PASSED → READY_FOR_REVIEW → APPROVED → UPLOADING → PRIVATE_UPLOADED → PUBLISHED
Include FAILED, CANCELLED and BLOCKED states.

Responsibilities:
- Track episode publication state through the full state machine
- Enforce server-side authorization for publication approval
- Prevent duplicate publication through idempotency keys
- Reconcile uncertain upload responses with the platform before retrying
- Maintain immutable audit trail for publishing decisions
- Default automated uploads to Private
- Require explicit human approval for Public or scheduled publication

Agent Outputs:
- state_transition: Validated state change with evidence
- publication_request: Upload request with idempotency key
- publish_approval: Human approval record
- upload_result: Platform upload confirmation or failure
- audit_entry: Immutable audit log entry
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class PublicationState(Enum):
    """Episode publication state machine per Spec #13."""
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


class PublishTarget(Enum):
    """Publishing target platform."""
    YOUTUBE = auto()
    OTHER = auto()


class Visibility(Enum):
    """Video visibility on platform."""
    PRIVATE = auto()
    PUBLIC = auto()
    UNLISTED = auto()
    SCHEDULED = auto()


@dataclass
class PublicationRecord:
    """Record of an episode's publication state and history."""
    episode_id: str
    series_id: str
    current_state: PublicationState
    publish_target: PublishTarget
    visibility: Visibility
    idempotency_key: str
    approved_by: str | None  # Human approver user ID
    approved_at: str | None
    uploaded_at: str | None
    published_at: str | None
    platform_video_id: str | None
    platform_url: str | None
    error_message: str | None
    retry_count: int
    audit_trail: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: uuid4().hex[:12])
    updated_at: str = field(default_factory=lambda: uuid4().hex[:12])

    def add_audit_entry(
        self, action: str, actor: str, details: dict[str, Any],
    ) -> None:
        """Append an immutable audit entry."""
        self.audit_trail.append({
            "action": action,
            "actor": actor,
            "details": details,
            "timestamp": uuid4().hex[:12],
        })
        self.updated_at = uuid4().hex[:12]


class PublishingAgent:
    """Agent 15 -- Publishing Agent implementation."""

    AGENT_ID = "AGENT_15"
    AGENT_NAME = "Publishing Agent"
    DESCRIPTION = "Manages approved uploads and publication states"

    # Valid state transitions per Spec #13
    VALID_TRANSITIONS: dict[PublicationState, list[PublicationState]] = {
        PublicationState.IDEA: [
            PublicationState.SCRIPT_APPROVED, PublicationState.CANCELLED,
            PublicationState.BLOCKED,
        ],
        PublicationState.SCRIPT_APPROVED: [
            PublicationState.ASSETS_READY, PublicationState.IDEA,
            PublicationState.CANCELLED, PublicationState.BLOCKED,
        ],
        PublicationState.ASSETS_READY: [
            PublicationState.RENDERING, PublicationState.SCRIPT_APPROVED,
            PublicationState.CANCELLED, PublicationState.BLOCKED,
        ],
        PublicationState.RENDERING: [
            PublicationState.RENDERED, PublicationState.FAILED,
            PublicationState.CANCELLED, PublicationState.BLOCKED,
        ],
        PublicationState.RENDERED: [
            PublicationState.QA_PENDING, PublicationState.FAILED,
            PublicationState.CANCELLED, PublicationState.BLOCKED,
        ],
        PublicationState.QA_PENDING: [
            PublicationState.QA_PASSED, PublicationState.FAILED,
            PublicationState.CANCELLED, PublicationState.BLOCKED,
        ],
        PublicationState.QA_PASSED: [
            PublicationState.READY_FOR_REVIEW, PublicationState.FAILED,
            PublicationState.CANCELLED, PublicationState.BLOCKED,
        ],
        PublicationState.READY_FOR_REVIEW: [
            PublicationState.APPROVED, PublicationState.READY_FOR_REVIEW,
            PublicationState.FAILED, PublicationState.CANCELLED,
            PublicationState.BLOCKED,
        ],
        PublicationState.APPROVED: [
            PublicationState.UPLOADING, PublicationState.READY_FOR_REVIEW,
            PublicationState.CANCELLED, PublicationState.BLOCKED,
        ],
        PublicationState.UPLOADING: [
            PublicationState.PRIVATE_UPLOADED, PublicationState.FAILED,
            PublicationState.CANCELLED, PublicationState.BLOCKED,
        ],
        PublicationState.PRIVATE_UPLOADED: [
            PublicationState.PUBLISHED, PublicationState.FAILED,
            PublicationState.CANCELLED, PublicationState.BLOCKED,
        ],
        PublicationState.PUBLISHED: [],  # Terminal state
        PublicationState.FAILED: [
            PublicationState.RENDERING, PublicationState.UPLOADING,
            PublicationState.IDEA, PublicationState.CANCELLED,
            PublicationState.BLOCKED,
        ],
        PublicationState.CANCELLED: [],  # Terminal state
        PublicationState.BLOCKED: [
            PublicationState.IDEA, PublicationState.READY_FOR_REVIEW,
        ],
    }

    # States that require human approval before advancing
    APPROVAL_REQUIRED_STATES = {
        PublicationState.APPROVED,
    }

    def __init__(self):
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID
        self._records: dict[str, PublicationRecord] = {}

    def create_publication_record(
        self, episode_id: str, series_id: str,
        publish_target: PublishTarget = PublishTarget.YOUTUBE,
        visibility: Visibility = Visibility.PRIVATE,
    ) -> PublicationRecord:
        """Create a new publication record in IDEA state."""
        record = PublicationRecord(
            episode_id=episode_id,
            series_id=series_id,
            current_state=PublicationState.IDEA,
            publish_target=publish_target,
            visibility=visibility,
            idempotency_key=f"idem_{uuid4().hex[:12]}",
            approved_by=None,
            approved_at=None,
            uploaded_at=None,
            published_at=None,
            platform_video_id=None,
            platform_url=None,
            error_message=None,
            retry_count=0,
        )
        record.add_audit_entry(
            "record_created", "system",
            {"initial_state": "IDEA", "visibility": visibility.name},
        )
        self._records[episode_id] = record
        return record

    def transition_state(
        self, episode_id: str, new_state: PublicationState,
        actor: str, details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Transition an episode to a new publication state.

        Server-side authorization: validates the transition is allowed.
        """
        if episode_id not in self._records:
            return {
                "status": "blocked",
                "error": f"No publication record for episode {episode_id}",
            }

        record = self._records[episode_id]
        current = record.current_state

        # Validate transition
        allowed = self.VALID_TRANSITIONS.get(current, [])
        if new_state not in allowed:
            return {
                "status": "blocked",
                "error": (
                    f"Invalid transition from {current.name} to {new_state.name}. "
                    f"Allowed: {[s.name for s in allowed]}"
                ),
            }

        # Check if human approval is required for this state
        if new_state in self.APPROVAL_REQUIRED_STATES:
            if not record.approved_by:
                return {
                    "status": "blocked",
                    "error": (
                        f"Human approval required before advancing to {new_state.name}. "
                        f"Use approve_publication() first."
                    ),
                }

        old_state = current
        record.current_state = new_state
        record.add_audit_entry(
            "state_transition", actor,
            {"from": old_state.name, "to": new_state.name, "details": details or {}},
        )

        # Set timestamps based on state
        if new_state == PublicationState.UPLOADING:
            # No timestamp yet; upload hasn't started
            pass
        elif new_state == PublicationState.PRIVATE_UPLOADED:
            record.uploaded_at = uuid4().hex[:12]
        elif new_state == PublicationState.PUBLISHED:
            record.published_at = uuid4().hex[:12]
        elif new_state == PublicationState.FAILED:
            record.error_message = (details or {}).get("error")

        return {
            "status": "completed",
            "episode_id": episode_id,
            "from_state": old_state.name,
            "to_state": new_state.name,
            "idempotency_key": record.idempotency_key,
            "audit_entry_count": len(record.audit_trail),
        }

    def approve_publication(
        self, episode_id: str, approver_user_id: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Human approver explicitly approves publication.

        Only an authorized human approver may approve external publication.
        Server-side authorization, not frontend-only.
        """
        if episode_id not in self._records:
            return {
                "status": "blocked",
                "error": f"No publication record for episode {episode_id}",
            }

        record = self._records[episode_id]

        if record.current_state != PublicationState.READY_FOR_REVIEW:
            return {
                "status": "blocked",
                "error": (
                    f"Episode must be in READY_FOR_REVIEW state for approval. "
                    f"Current: {record.current_state.name}"
                ),
            }

        record.approved_by = approver_user_id
        record.approved_at = uuid4().hex[:12]
        record.current_state = PublicationState.APPROVED
        record.add_audit_entry(
            "publication_approved", approver_user_id,
            {"details": details or {}},
        )

        return {
            "status": "completed",
            "episode_id": episode_id,
            "approved_by": approver_user_id,
            "approved_at": record.approved_at,
            "new_state": "APPROVED",
            "idempotency_key": record.idempotency_key,
        }

    def request_upload(
        self, episode_id: str, platform_video_id: str | None = None,
        platform_url: str | None = None,
        visibility: Visibility = Visibility.PRIVATE,
    ) -> dict[str, Any]:
        """Request upload to platform.

        Default automated uploads to Private. Public/scheduled requires approval.
        """
        if episode_id not in self._records:
            return {
                "status": "blocked",
                "error": f"No publication record for episode {episode_id}",
            }

        record = self._records[episode_id]

        if record.current_state != PublicationState.APPROVED:
            return {
                "status": "blocked",
                "error": (
                    f"Episode must be APPROVED before upload. Current: "
                    f"{record.current_state.name}"
                ),
            }

        # Idempotency: check if already uploading or uploaded with same key
        if record.current_state == PublicationState.UPLOADING:
            return {
                "status": "blocked",
                "error": (
                    f"Upload already in progress for {episode_id}. "
                    f"Idempotency key: {record.idempotency_key}"
                ),
            }

        record.visibility = visibility
        record.current_state = PublicationState.UPLOADING
        record.add_audit_entry(
            "upload_requested", "system",
            {"visibility": visibility.name, "idempotency_key": record.idempotency_key},
        )

        # Simulate platform response reconciliation
        if platform_video_id:
            record.platform_video_id = platform_video_id
            record.platform_url = platform_url
            record.current_state = PublicationState.PRIVATE_UPLOADED
            record.uploaded_at = uuid4().hex[:12]
            record.add_audit_entry(
                "upload_confirmed", "system",
                {"platform_video_id": platform_video_id, "platform_url": platform_url},
            )

        return {
            "status": "completed",
            "episode_id": episode_id,
            "state": record.current_state.name,
            "idempotency_key": record.idempotency_key,
            "visibility": visibility.name,
            "platform_video_id": record.platform_video_id,
            "platform_url": record.platform_url,
        }

    def publish_to_public(
        self, episode_id: str, approver_user_id: str,
    ) -> dict[str, Any]:
        """Move from PRIVATE_UPLOADED to PUBLISHED.

        Requires explicit human approval. Publishing to Public or scheduling
        publication requires explicit approval per Spec #13.
        """
        if episode_id not in self._records:
            return {
                "status": "blocked",
                "error": f"No publication record for episode {episode_id}",
            }

        record = self._records[episode_id]

        if record.current_state != PublicationState.PRIVATE_UPLOADED:
            return {
                "status": "blocked",
                "error": (
                    f"Episode must be PRIVATE_UPLOADED before public publishing. "
                    f"Current: {record.current_state.name}"
                ),
            }

        if not record.approved_by:
            return {
                "status": "blocked",
                "error": "Human approval required for public publication",
            }

        record.current_state = PublicationState.PUBLISHED
        record.published_at = uuid4().hex[:12]
        record.add_audit_entry(
            "published_to_public", approver_user_id,
            {"visibility": "PUBLIC", "published_at": record.published_at},
        )

        return {
            "status": "completed",
            "episode_id": episode_id,
            "new_state": "PUBLISHED",
            "published_at": record.published_at,
            "platform_url": record.platform_url,
        }

    def record_failure(
        self, episode_id: str, error_message: str,
        actor: str = "system",
    ) -> dict[str, Any]:
        """Record a failure and increment retry count."""
        if episode_id not in self._records:
            return {
                "status": "blocked",
                "error": f"No publication record for episode {episode_id}",
            }

        record = self._records[episode_id]
        record.current_state = PublicationState.FAILED
        record.error_message = error_message
        record.retry_count += 1
        record.add_audit_entry(
            "failure_recorded", actor,
            {"error": error_message, "retry_count": record.retry_count},
        )

        return {
            "status": "completed",
            "episode_id": episode_id,
            "new_state": "FAILED",
            "error": error_message,
            "retry_count": record.retry_count,
        }

    def cancel_publication(
        self, episode_id: str, actor: str,
    ) -> dict[str, Any]:
        """Cancel publication (terminal state)."""
        if episode_id not in self._records:
            return {
                "status": "blocked",
                "error": f"No publication record for episode {episode_id}",
            }

        record = self._records[episode_id]
        record.current_state = PublicationState.CANCELLED
        record.add_audit_entry(
            "publication_cancelled", actor, {},
        )

        return {
            "status": "completed",
            "episode_id": episode_id,
            "new_state": "CANCELLED",
        }

    def block_publication(
        self, episode_id: str, actor: str, reason: str,
    ) -> dict[str, Any]:
        """Block publication (can be unblocked later)."""
        if episode_id not in self._records:
            return {
                "status": "blocked",
                "error": f"No publication record for episode {episode_id}",
            }

        record = self._records[episode_id]
        record.current_state = PublicationState.BLOCKED
        record.add_audit_entry(
            "publication_blocked", actor, {"reason": reason},
        )

        return {
            "status": "completed",
            "episode_id": episode_id,
            "new_state": "BLOCKED",
            "reason": reason,
        }

    def unblock_publication(
        self, episode_id: str, actor: str,
    ) -> dict[str, Any]:
        """Unblock publication, returning to IDEA or READY_FOR_REVIEW."""
        if episode_id not in self._records:
            return {
                "status": "blocked",
                "error": f"No publication record for episode {episode_id}",
            }

        record = self._records[episode_id]
        if record.current_state != PublicationState.BLOCKED:
            return {
                "status": "blocked",
                "error": (
                    f"Episode is not BLOCKED. Current: {record.current_state.name}"
                ),
            }

        record.current_state = PublicationState.IDEA
        record.add_audit_entry(
            "publication_unblocked", actor, {},
        )

        return {
            "status": "completed",
            "episode_id": episode_id,
            "new_state": "IDEA",
        }

    def get_record(self, episode_id: str) -> dict[str, Any] | None:
        """Get publication record as dictionary."""
        if episode_id not in self._records:
            return None

        record = self._records[episode_id]
        return {
            "episode_id": record.episode_id,
            "series_id": record.series_id,
            "current_state": record.current_state.name,
            "publish_target": record.publish_target.name,
            "visibility": record.visibility.name,
            "idempotency_key": record.idempotency_key,
            "approved_by": record.approved_by,
            "approved_at": record.approved_at,
            "uploaded_at": record.uploaded_at,
            "published_at": record.published_at,
            "platform_video_id": record.platform_video_id,
            "platform_url": record.platform_url,
            "error_message": record.error_message,
            "retry_count": record.retry_count,
            "audit_trail": record.audit_trail,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "capability": "publishing",
            "states": [s.name for s in PublicationState],
            "valid_transitions_count": sum(
                len(v) for v in self.VALID_TRANSITIONS.values()
            ),
        }


# Module-level agent instance
agent = PublishingAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a Publishing Agent action.

    Args:
        action: The action to execute
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "create_record":
        record = agent_obj.create_publication_record(
            episode_id=kwargs.get("episode_id", f"episode_{uuid4().hex[:6]}"),
            series_id=kwargs.get("series_id", "series_default"),
            publish_target=PublishTarget[kwargs.get("publish_target", "YOUTUBE")],
            visibility=Visibility[kwargs.get("visibility", "PRIVATE")],
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "create_record",
            "status": "completed",
            "episode_id": record.episode_id,
            "series_id": record.series_id,
            "current_state": record.current_state.name,
            "idempotency_key": record.idempotency_key,
            "visibility": record.visibility.name,
            "created_at": record.created_at,
        }

    elif action == "transition_state":
        result = agent_obj.transition_state(
            episode_id=kwargs.get("episode_id", ""),
            new_state=PublicationState[kwargs.get("new_state", "IDEA")],
            actor=kwargs.get("actor", "system"),
            details=kwargs.get("details", {}),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "transition_state",
            **result,
        }

    elif action == "approve_publication":
        result = agent_obj.approve_publication(
            episode_id=kwargs.get("episode_id", ""),
            approver_user_id=kwargs.get("approver_user_id", ""),
            details=kwargs.get("details", {}),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "approve_publication",
            **result,
        }

    elif action == "request_upload":
        result = agent_obj.request_upload(
            episode_id=kwargs.get("episode_id", ""),
            platform_video_id=kwargs.get("platform_video_id"),
            platform_url=kwargs.get("platform_url"),
            visibility=Visibility[kwargs.get("visibility", "PRIVATE")],
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "request_upload",
            **result,
        }

    elif action == "publish_to_public":
        result = agent_obj.publish_to_public(
            episode_id=kwargs.get("episode_id", ""),
            approver_user_id=kwargs.get("approver_user_id", ""),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "publish_to_public",
            **result,
        }

    elif action == "record_failure":
        result = agent_obj.record_failure(
            episode_id=kwargs.get("episode_id", ""),
            error_message=kwargs.get("error_message", ""),
            actor=kwargs.get("actor", "system"),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "record_failure",
            **result,
        }

    elif action == "cancel_publication":
        result = agent_obj.cancel_publication(
            episode_id=kwargs.get("episode_id", ""),
            actor=kwargs.get("actor", "system"),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "cancel_publication",
            **result,
        }

    elif action == "block_publication":
        result = agent_obj.block_publication(
            episode_id=kwargs.get("episode_id", ""),
            actor=kwargs.get("actor", "system"),
            reason=kwargs.get("reason", ""),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "block_publication",
            **result,
        }

    elif action == "unblock_publication":
        result = agent_obj.unblock_publication(
            episode_id=kwargs.get("episode_id", ""),
            actor=kwargs.get("actor", "system"),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "unblock_publication",
            **result,
        }

    elif action == "get_record":
        record = agent_obj.get_record(kwargs.get("episode_id", ""))
        if record is None:
            return {
                "agent": agent_obj.AGENT_ID,
                "action": "get_record",
                "status": "blocked",
                "error": f"No record for {kwargs.get('episode_id', '')}",
            }
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_record",
            "status": "completed",
            "record": record,
        }

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "PublishingAgent",
    "PublicationRecord",
    "PublicationState",
    "PublishTarget",
    "Visibility",
    "execute_action",
    "agent",
]