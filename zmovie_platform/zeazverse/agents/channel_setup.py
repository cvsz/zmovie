"""Agent 01 -- Channel Setup Agent

Manages setup guidance, configuration validation and readiness
for the ZEAZVERSE YouTube channel per Specification Section 5.

Responsibilities:
- Provide 15-item YouTube channel setup checklist
- Track status of each setup item: Completed, Verified, Pending, Blocked, Requires user action
- Validate channel configuration readiness
- Never claim a YouTube channel was created unless YouTube confirms it
- Do not attempt to automate account creation, verification challenges,
  or authorization flows in ways unsupported by Google

Agent Outputs:
- setup_checklist: 15 checklist items with status
- channel_readiness: Overall readiness assessment
- setup_guidance: Step-by-step setup instructions
- status_dashboard: Current setup status summary
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class ItemStatus(Enum):
    """Setup checklist item status per Spec #5."""
    COMPLETED = auto()
    VERIFIED = auto()
    PENDING = auto()
    BLOCKED = auto()
    REQUIRES_USER_ACTION = auto()


class ChannelReadiness(Enum):
    """Overall channel readiness level."""
    NOT_STARTED = auto()
    PARTIAL = auto()
    READY_FOR_VERIFICATION = auto()
    READY = auto()


@dataclass
class ChecklistItem:
    """Single item in the YouTube channel setup checklist."""
    item_id: str
    item_number: int
    title: str
    description: str
    status: ItemStatus
    requires_user_action: bool
    evidence: str | None = None
    notes: str = ""
    updated_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class ChannelSetup:
    """Complete channel setup state."""
    setup_id: str
    channel_id: str | None
    channel_handle: str | None
    channel_name: str
    items: list[ChecklistItem]
    readiness: ChannelReadiness
    owner_user_id: str | None
    created_at: str = field(default_factory=lambda: uuid4().hex[:12])
    updated_at: str = field(default_factory=lambda: uuid4().hex[:12])


# The 15 required setup checklist items per Spec #5
SETUP_CHECKLIST_TEMPLATE = [
    {
        "number": 1,
        "title": "Secure Google account ownership",
        "description": (
            "Verify ownership of the Google account that will manage "
            "the ZEAZVERSE YouTube channel. Account must be secured "
            "with a strong password and recovery options."
        ),
        "requires_user_action": True,
    },
    {
        "number": 2,
        "title": "Enable multi-factor authentication",
        "description": (
            "Enable MFA/2FA on the Google account to protect against "
            "unauthorized access. This is required before channel creation."
        ),
        "requires_user_action": True,
    },
    {
        "number": 3,
        "title": "Create the YouTube channel through authorized user flow",
        "description": (
            "Create the YouTube channel using the official YouTube "
            "channel creation flow. Channel name: ZEAZVERSE, "
            "Preferred handle: @ZEAZVERSE."
        ),
        "requires_user_action": True,
    },
    {
        "number": 4,
        "title": "Confirm channel ID and actual handle",
        "description": (
            "Confirm the actual channel ID (UC...) and handle "
            "(@ZEAZVERSE or as assigned) after channel creation. "
            "Never claim a channel exists unless YouTube confirms it."
        ),
        "requires_user_action": True,
    },
    {
        "number": 5,
        "title": "Upload branding assets",
        "description": (
            "Upload logo, profile avatar, YouTube banner, and video "
            "watermark. All assets must be original ZEAZVERSE brand "
            "assets per Spec #3 brand identity."
        ),
        "requires_user_action": False,
    },
    {
        "number": 6,
        "title": "Configure channel description",
        "description": (
            "Set channel description: 'Original AI cinematic stories "
            "and virtual idols from Thailand. Characters: LALIN, "
            "NICHA, PIM, YADA.'"
        ),
        "requires_user_action": False,
    },
    {
        "number": 7,
        "title": "Configure country and language",
        "description": (
            "Set channel country and language where supported by "
            "YouTube. Primary audience: Global English-speaking "
            "viewers with Thai localization."
        ),
        "requires_user_action": False,
    },
    {
        "number": 8,
        "title": "Configure audience settings",
        "description": (
            "Configure audience settings based on actual content. "
            "Specify whether content is made for kids or not."
        ),
        "requires_user_action": False,
    },
    {
        "number": 9,
        "title": "Complete channel feature eligibility requirements",
        "description": (
            "Complete all requirements to unlock channel features "
            "such as custom thumbnails, external links, and "
            "monetization eligibility."
        ),
        "requires_user_action": False,
    },
    {
        "number": 10,
        "title": "Configure upload defaults",
        "description": (
            "Set default upload settings including privacy (Private "
            "by default), category, language, and comments."
        ),
        "requires_user_action": False,
    },
    {
        "number": 11,
        "title": "Configure playlists",
        "description": (
            "Create and configure playlists for organizing content "
            "by character (LALIN, NICHA, PIM, YADA) and theme."
        ),
        "requires_user_action": False,
    },
    {
        "number": 12,
        "title": "Configure channel homepage",
        "description": (
            "Configure channel homepage layout including featured "
            "video, channel trailer, and section organization."
        ),
        "requires_user_action": False,
    },
    {
        "number": 13,
        "title": "Configure team permissions",
        "description": (
            "Configure team member permissions and roles for channel "
            "management. Apply least-privilege access per Spec #16."
        ),
        "requires_user_action": False,
    },
    {
        "number": 14,
        "title": "Configure moderation and community settings",
        "description": (
            "Configure comment moderation, community posts settings, "
            "and blocked words list."
        ),
        "requires_user_action": False,
    },
    {
        "number": 15,
        "title": "Verify publishing capabilities",
        "description": (
            "Verify that the channel can publish videos. Start with "
            "private uploads per Spec #13 publishing approval flow."
        ),
        "requires_user_action": False,
    },
]


class ChannelSetupAgent:
    """Agent 01 -- Channel Setup Agent implementation."""

    AGENT_ID = "AGENT_01"
    AGENT_NAME = "Channel Setup Agent"
    DESCRIPTION = "Manages setup guidance, configuration validation and readiness"

    def __init__(self):
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID
        self._setups: dict[str, ChannelSetup] = {}

    def initialize_setup(
        self, channel_name: str = "ZEAZVERSE",
        owner_user_id: str | None = None,
    ) -> ChannelSetup:
        """Initialize a new channel setup with all 15 checklist items."""
        setup_id = f"setup_{uuid4().hex[:8]}"

        items = [
            ChecklistItem(
                item_id=f"item_{item['number']:02d}",
                item_number=item["number"],
                title=item["title"],
                description=item["description"],
                status=ItemStatus.PENDING,
                requires_user_action=item["requires_user_action"],
            )
            for item in SETUP_CHECKLIST_TEMPLATE
        ]

        setup = ChannelSetup(
            setup_id=setup_id,
            channel_id=None,
            channel_handle=None,
            channel_name=channel_name,
            items=items,
            readiness=ChannelReadiness.NOT_STARTED,
            owner_user_id=owner_user_id,
        )
        self._setups[setup_id] = setup
        return setup

    def update_item_status(
        self, setup_id: str, item_number: int, status: ItemStatus,
        evidence: str | None = None, notes: str = "",
    ) -> dict[str, Any]:
        """Update the status of a checklist item."""
        if setup_id not in self._setups:
            return {
                "status": "blocked",
                "error": f"Setup {setup_id} not found",
            }

        setup = self._setups[setup_id]
        item = next(
            (i for i in setup.items if i.item_number == item_number), None
        )
        if item is None:
            return {
                "status": "blocked",
                "error": f"Item {item_number} not found in setup {setup_id}",
            }

        # Items 1-4 require user action - cannot be auto-completed
        if item.requires_user_action and status in [
            ItemStatus.COMPLETED, ItemStatus.VERIFIED
        ] and not evidence:
            return {
                "status": "blocked",
                "error": (
                    f"Item {item_number} requires user action and evidence. "
                    f"Cannot auto-complete items 1-4 per Spec #5."
                ),
            }

        old_status = item.status
        item.status = status
        item.evidence = evidence
        item.notes = notes
        item.updated_at = uuid4().hex[:12]
        setup.updated_at = uuid4().hex[:12]

        # Recalculate overall readiness
        setup.readiness = self._calculate_readiness(setup)

        return {
            "status": "completed",
            "setup_id": setup_id,
            "item_number": item_number,
            "from_status": old_status.name,
            "to_status": status.name,
            "readiness": setup.readiness.name,
        }

    def confirm_channel(
        self, setup_id: str, channel_id: str, channel_handle: str,
        confirmed_by: str,
    ) -> dict[str, Any]:
        """Confirm YouTube channel creation.

        Per Spec #5: Never claim a YouTube channel was created unless
        YouTube confirms it. This records the confirmation evidence.
        """
        if setup_id not in self._setups:
            return {
                "status": "blocked",
                "error": f"Setup {setup_id} not found",
            }

        setup = self._setups[setup_id]

        # Items 1-4 must be verified before channel confirmation
        for item_num in [1, 2, 3, 4]:
            item = next(
                (i for i in setup.items if i.item_number == item_num), None
            )
            if item is None or item.status != ItemStatus.VERIFIED:
                return {
                    "status": "blocked",
                    "error": (
                        f"Item {item_num} must be VERIFIED before "
                        f"channel confirmation. Current: "
                        f"{item.status.name if item else 'missing'}"
                    ),
                }

        setup.channel_id = channel_id
        setup.channel_handle = channel_handle
        setup.owner_user_id = confirmed_by
        setup.updated_at = uuid4().hex[:12]
        setup.readiness = self._calculate_readiness(setup)

        return {
            "status": "completed",
            "setup_id": setup_id,
            "channel_id": channel_id,
            "channel_handle": channel_handle,
            "confirmed_by": confirmed_by,
            "readiness": setup.readiness.name,
        }

    def get_setup(self, setup_id: str) -> dict[str, Any] | None:
        """Get channel setup details."""
        if setup_id not in self._setups:
            return None

        setup = self._setups[setup_id]
        return {
            "setup_id": setup_id,
            "channel_id": setup.channel_id,
            "channel_handle": setup.channel_handle,
            "channel_name": setup.channel_name,
            "readiness": setup.readiness.name,
            "owner_user_id": setup.owner_user_id,
            "items": [
                {
                    "item_id": i.item_id,
                    "item_number": i.item_number,
                    "title": i.title,
                    "description": i.description,
                    "status": i.status.name,
                    "requires_user_action": i.requires_user_action,
                    "evidence": i.evidence,
                    "notes": i.notes,
                    "updated_at": i.updated_at,
                }
                for i in setup.items
            ],
            "created_at": setup.created_at,
            "updated_at": setup.updated_at,
        }

    def get_status_dashboard(self) -> dict[str, Any]:
        """Get overall setup status dashboard."""
        if not self._setups:
            return {
                "status": "no_setups",
                "message": "No channel setups initialized",
            }

        # Return the most recent setup
        latest_setup_id = max(
            self._setups.keys(),
            key=lambda sid: self._setups[sid].updated_at,
        )
        setup = self._setups[latest_setup_id]

        completed = sum(
            1 for i in setup.items if i.status == ItemStatus.COMPLETED
        )
        verified = sum(
            1 for i in setup.items if i.status == ItemStatus.VERIFIED
        )
        pending = sum(
            1 for i in setup.items if i.status == ItemStatus.PENDING
        )
        blocked = sum(
            1 for i in setup.items if i.status == ItemStatus.BLOCKED
        )
        requires_action = sum(
            1 for i in setup.items
            if i.status == ItemStatus.REQUIRES_USER_ACTION
        )

        return {
            "status": "completed",
            "setup_id": latest_setup_id,
            "channel_name": setup.channel_name,
            "channel_id": setup.channel_id,
            "channel_handle": setup.channel_handle,
            "readiness": setup.readiness.name,
            "total_items": len(setup.items),
            "completed": completed,
            "verified": verified,
            "pending": pending,
            "blocked": blocked,
            "requires_user_action": requires_action,
            "owner_user_id": setup.owner_user_id,
            "updated_at": setup.updated_at,
        }

    def _calculate_readiness(self, setup: ChannelSetup) -> ChannelReadiness:
        """Calculate overall channel readiness from item statuses."""
        if not setup.items:
            return ChannelReadiness.NOT_STARTED

        statuses = [i.status for i in setup.items]

        if all(s == ItemStatus.VERIFIED for s in statuses):
            return ChannelReadiness.READY
        if any(s == ItemStatus.BLOCKED for s in statuses):
            return ChannelReadiness.PARTIAL
        if any(s in [ItemStatus.COMPLETED, ItemStatus.VERIFIED] for s in statuses):
            return ChannelReadiness.PARTIAL
        if any(s == ItemStatus.PENDING for s in statuses):
            return ChannelReadiness.NOT_STARTED

        return ChannelReadiness.PARTIAL

    def get_setup_guidance(self) -> dict[str, Any]:
        """Get step-by-step setup guidance."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "total_items": len(SETUP_CHECKLIST_TEMPLATE),
            "items": [
                {
                    "item_number": item["number"],
                    "title": item["title"],
                    "requires_user_action": item["requires_user_action"],
                }
                for item in SETUP_CHECKLIST_TEMPLATE
            ],
            "important_notes": [
                "Items 1-4 require genuine user action via Google OAuth flow",
                "Never claim a YouTube channel was created unless YouTube confirms it",
                "Do not automate account creation, verification challenges, or authorization flows",
                "External publishing defaults to Private per Spec #13",
            ],
        }

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "capability": "channel_setup",
            "checklist_items": len(SETUP_CHECKLIST_TEMPLATE),
            "statuses": [s.name for s in ItemStatus],
        }


# Module-level agent instance
agent = ChannelSetupAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a Channel Setup Agent action.

    Args:
        action: The action to execute
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "initialize_setup":
        setup = agent_obj.initialize_setup(
            channel_name=kwargs.get("channel_name", "ZEAZVERSE"),
            owner_user_id=kwargs.get("owner_user_id"),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "initialize_setup",
            "status": "completed",
            "setup_id": setup.setup_id,
            "channel_name": setup.channel_name,
            "readiness": setup.readiness.name,
            "total_items": len(setup.items),
        }

    elif action == "update_item_status":
        result = agent_obj.update_item_status(
            setup_id=kwargs.get("setup_id", ""),
            item_number=kwargs.get("item_number", 0),
            status=ItemStatus[kwargs.get("status", "PENDING")],
            evidence=kwargs.get("evidence"),
            notes=kwargs.get("notes", ""),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "update_item_status",
            **result,
        }

    elif action == "confirm_channel":
        result = agent_obj.confirm_channel(
            setup_id=kwargs.get("setup_id", ""),
            channel_id=kwargs.get("channel_id", ""),
            channel_handle=kwargs.get("channel_handle", ""),
            confirmed_by=kwargs.get("confirmed_by", ""),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "confirm_channel",
            **result,
        }

    elif action == "get_setup":
        setup = agent_obj.get_setup(kwargs.get("setup_id", ""))
        if setup is None:
            return {
                "agent": agent_obj.AGENT_ID,
                "action": "get_setup",
                "status": "blocked",
                "error": "Setup not found",
            }
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_setup",
            "status": "completed",
            "setup": setup,
        }

    elif action == "get_status_dashboard":
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_status_dashboard",
            **agent_obj.get_status_dashboard(),
        }

    elif action == "get_setup_guidance":
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_setup_guidance",
            "status": "completed",
            **agent_obj.get_setup_guidance(),
        }

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "ChannelSetupAgent",
    "ChannelSetup",
    "ChecklistItem",
    "ItemStatus",
    "ChannelReadiness",
    "SETUP_CHECKLIST_TEMPLATE",
    "execute_action",
    "agent",
]