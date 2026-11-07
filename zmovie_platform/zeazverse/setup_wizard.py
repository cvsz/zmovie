"""YouTube Channel Setup Wizard for ZEAZVERSE.

Implements the channel setup checklist from ZEAZVERSE Specification Section 5.
Distinguishes: Completed, Verified, Pending, Blocked, Requires user action.

Never fabricate external actions, successful rendering, API authentication,
publication, analytics, or production readiness.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from zmovie_platform.zeazverse.store import ensure_tables, utcnow


class ChannelSetupStatus(Enum):
    """Status for each checklist item."""
    COMPLETED = auto()
    VERIFIED = auto()
    PENDING = auto()
    BLOCKED = auto()
    REQUIRES_USER_ACTION = auto()


@dataclass
class ChecklistItem:
    """A single checklist item with status and metadata."""
    id: int
    label: str
    description: str = ""
    status: ChannelSetupStatus = ChannelSetupStatus.PENDING
    evidence: dict = field(default_factory=dict)
    requires_user_action: bool = False
    verified_at: str | None = None
    completed_at: str | None = None


# 15 required checklist items from ZEAZVERSE Specification Section 5
CHECKLIST: tuple[ChecklistItem, ...] = (
    ChecklistItem(
        id=1,
        label="Secure Google account ownership",
        description="Confirm Google account that will own the ZEAZVERSE YouTube channel",
        status=ChannelSetupStatus.PENDING,
        requires_user_action=True,
    ),
    ChecklistItem(
        id=2,
        label="Enable multi-factor authentication",
        description="Enable 2FA on the Google account for security",
        status=ChannelSetupStatus.PENDING,
        requires_user_action=True,
    ),
    ChecklistItem(
        id=3,
        label="Create the YouTube channel through the authorized user flow",
        description="Create channel via Google's authorized channel creation flow",
        status=ChannelSetupStatus.PENDING,
        requires_user_action=True,
        # Per spec: Never claim channel was created unless YouTube confirms it
    ),
    ChecklistItem(
        id=4,
        label="Confirm channel ID and actual handle",
        description="Verify the channel ID and @handle match the intended ZEAZVERSE identity",
        status=ChannelSetupStatus.PENDING,
        requires_user_action=True,
    ),
    ChecklistItem(
        id=5,
        label="Upload branding assets",
        description="Upload logo, profile avatar, YouTube banner, video watermark",
        status=ChannelSetupStatus.PENDING,
        evidence={},
    ),
    ChecklistItem(
        id=6,
        label="Configure channel description",
        description='Set channel description: "Original AI cinematic stories and virtual idols from Thailand."',
        status=ChannelSetupStatus.PENDING,
    ),
    ChecklistItem(
        id=7,
        label="Configure country and language where supported",
        description="Set country and language preferences for the channel",
        status=ChannelSetupStatus.PENDING,
    ),
    ChecklistItem(
        id=8,
        label="Configure audience settings based on actual content",
        description="Set audience demographics and content classification",
        status=ChannelSetupStatus.PENDING,
    ),
    ChecklistItem(
        id=9,
        label="Complete channel feature eligibility requirements",
        description="Complete all YouTube feature eligibility requirements",
        status=ChannelSetupStatus.PENDING,
    ),
    ChecklistItem(
        id=10,
        label="Configure upload defaults",
        description="Set default upload settings (category, tags, defaults)",
        status=ChannelSetupStatus.PENDING,
    ),
    ChecklistItem(
        id=11,
        label="Configure playlists",
        description="Set up playlists for LALIN, NICHA, PIM, YADA content series",
        status=ChannelSetupStatus.PENDING,
    ),
    ChecklistItem(
        id=12,
        label="Configure channel homepage",
        description="Configure the channel's featured sections and layout",
        status=ChannelSetupStatus.PENDING,
    ),
    ChecklistItem(
        id=13,
        label="Configure team permissions",
        description="Set up team member roles and permissions (if applicable)",
        status=ChannelSetupStatus.PENDING,
    ),
    ChecklistItem(
        id=14,
        label="Configure moderation and community settings",
        description="Set up comment moderation, chat settings, community features",
        status=ChannelSetupStatus.PENDING,
    ),
    ChecklistItem(
        id=15,
        label="Verify publishing capabilities",
        description="Confirm the channel can publish videos (initially Private by default)",
        status=ChannelSetupStatus.PENDING,
    ),
)


@dataclass
class ChannelSetupDashboard:
    """Dashboard showing overall channel setup status."""
    channel_handle: str = "ZEAZVERSE"
    total_items: int = 15
    completed: int = 0
    verified: int = 0
    pending: int = 0
    blocked: int = 0
    requires_user_action: int = 0

    def compute_stats(self) -> None:
        """Recalculate statistics from the checklist."""
        self.completed = sum(
            1 for item in CHECKLIST if item.status == ChannelSetupStatus.COMPLETED
        )
        self.verified = sum(
            1 for item in CHECKLIST if item.status == ChannelSetupStatus.VERIFIED
        )
        self.pending = sum(
            1 for item in CHECKLIST if item.status == ChannelSetupStatus.PENDING
        )
        self.blocked = sum(
            1 for item in CHECKLIST if item.status == ChannelSetupStatus.BLOCKED
        )
        self.requires_user_action = sum(
            1 for item in CHECKLIST if item.requires_user_action
        )

    def get_status_summary(self) -> str:
        """Get a human-readable status summary."""
        self.compute_stats()
        lines = [
            f"ZEAZVERSE YouTube Channel Setup: {self.channel_handle}",
            f"",
            f"  Total items: {self.total_items}",
            f"  Completed: {self.completed}",
            f"  Verified: {self.verified}",
            f"  Pending: {self.pending}",
            f"  Blocked: {self.blocked}",
            f"  Requires user action: {self.requires_user_action}",
            f"",
            f"Status legend:",
            f"  ✓ COMPLETED - Item fully done",
            f"  ✓ VERIFIED - Item confirmed/validated",
            f"  ⏳ PENDING - Awaiting action",
            f"  ⛔ BLOCKED - Cannot proceed",
            f"  ⚠ REQUIRES USER ACTION - Needs human interaction",
            f"",
        ]
        # Detail per item
        for item in CHECKLIST:
            symbol = {
                ChannelSetupStatus.COMPLETED: "✓",
                ChannelSetupStatus.VERIFIED: "✓",
                ChannelSetupStatus.PENDING: "⏳",
                ChannelSetupStatus.BLOCKED: "⛔",
                ChannelSetupStatus.REQUIRES_USER_ACTION: "⚠",
            }[item.status]
            lines.append(
                f"  {symbol} Item {item.id}: {item.label}"
                + (f" (REQUIRES USER ACTION)" if item.requires_user_action else "")
            )
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage/audit."""
        self.compute_stats()
        return {
            "channel_handle": self.channel_handle,
            "statistics": {
                "total": self.total_items,
                "completed": self.completed,
                "verified": self.verified,
                "pending": self.pending,
                "blocked": self.blocked,
                "requires_user_action": self.requires_user_action,
            },
            "checklist": [
                {
                    "id": item.id,
                    "label": item.label,
                    "description": item.description,
                    "status": item.status.name,
                    "evidence": item.evidence,
                    "requires_user_action": item.requires_user_action,
                    "completed_at": item.completed_at,
                    "verified_at": item.verified_at,
                }
                for item in CHECKLIST
            ],
        }


def ensure_setup_tables() -> None:
    """Ensure the zeazverse_setup_status table exists."""
    ensure_tables()  # This creates all zeazverse_* tables including setup tracking


def update_checklist_status(
    item_id: int,
    status: ChannelSetupStatus,
    evidence: dict | None = None,
    verified_by: str | None = None,
) -> bool:
    """Update a single checklist item status.

    Args:
        item_id: The checklist item ID (1-15)
        status: New status to set
        evidence: Optional evidence dict for verification
        verified_by: Optional identifier of what verified the change

    Returns:
        True if the update was applied successfully
    """
    updated = False
    for item in CHECKLIST:
        if item.id == item_id:
            old_status = item.status
            item.status = status

            if evidence is not None:
                item.evidence = evidence

            if status == ChannelSetupStatus.COMPLETED:
                item.completed_at = utcnow()
            if status == ChannelSetupStatus.VERIFIED:
                item.verified_at = utcnow()

            updated = True
            # Audit log could be written here
            # _audit(...)
            break

    return updated


def get_checklist_item(item_id: int) -> ChecklistItem | None:
    """Get a specific checklist item by ID."""
    for item in CHECKLIST:
        if item.id == item_id:
            return item
    return None


def get_dashboard() -> ChannelSetupDashboard:
    """Get the current setup dashboard."""
    dashboard = ChannelSetupDashboard()
    dashboard.compute_stats()
    return dashboard


# Module-level initialization - ensure tables are available
ensure_setup_tables()

# Print initialization summary on import (for development visibility)
if __name__ != "__main__":
    dashboard = get_dashboard()
    print(dashboard.get_status_summary())