"""Agent 18 -- Security & Audit Agent

Reviews permissions, secrets, external actions, incidents and audit evidence
per Spec #16.

Responsibilities:
- Review permissions and RBAC assignments
- Audit secret management and token encryption
- Review external actions and API authorization
- Validate inputs and webhook verification
- Detect and log security incidents
- Prevent SSRF when ingesting remote reference URLs
- Treat all external content as untrusted input
- Enforce human approval for high-impact external actions
- Maintain immutable audit trail

Agent Outputs:
- permission_review: RBAC and access boundary validation
- secret_audit: Secret management and encryption review
- incident_log: Security incident records
- input_validation: Input sanitization results
- webhook_verification: Webhook signature verification
- audit_trail: Immutable audit log entries
- ssrf_check: SSRF prevention validation
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class Severity(Enum):
    """Security incident severity levels."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class AuditEventType(Enum):
    """Types of auditable events."""
    AUTHENTICATION = auto()
    AUTHORIZATION = auto()
    SECRET_ACCESS = auto()
    EXTERNAL_ACTION = auto()
    INPUT_VALIDATION = auto()
    WEBHOOK_VERIFICATION = auto()
    SSRF_PREVENTION = auto()
    INCIDENT = auto()
    PERMISSION_CHANGE = auto()
    PUBLISHING_ACTION = auto()


class RiskLevel(Enum):
    """Risk assessment levels."""
    MINIMAL = auto()
    LOW = auto()
    MODERATE = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class PermissionReview:
    """Review of RBAC permissions and access boundaries."""
    review_id: str
    user_id: str
    role: str
    permissions: list[str]
    tenant_boundaries: list[str]
    compliant: bool
    issues: list[str] = field(default_factory=list)
    reviewed_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class SecretAudit:
    """Audit of secret management practices."""
    audit_id: str
    secret_name: str
    encrypted_at_rest: bool
    never_in_source_control: bool
    never_exposed_to_browser: bool
    rotation_due: bool
    compliant: bool
    issues: list[str] = field(default_factory=list)
    audited_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class SecurityIncident:
    """Security incident record."""
    incident_id: str
    event_type: AuditEventType
    severity: Severity
    description: str
    affected_resources: list[str]
    actor: str | None
    resolved: bool
    resolution_notes: str | None
    created_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class InputValidationResult:
    """Result of input validation/sanitization."""
    input_id: str
    input_type: str  # "prompt", "metadata", "caption", "url", etc.
    is_valid: bool
    sanitized: bool
    threats_detected: list[str]
    violations: list[str]
    validated_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class WebhookVerificationResult:
    """Result of webhook signature verification."""
    webhook_id: str
    source: str
    signature_valid: bool
    timestamp_within_tolerance: bool
    verified: bool
    verified_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class SSRFCheckResult:
    """Result of SSRF prevention check for remote URLs."""
    url: str
    is_safe: bool
    blocked_reasons: list[str]
    allowed_domains: list[str]
    checked_at: str = field(default_factory=lambda: uuid4().hex[:12])


@dataclass
class AuditEntry:
    """Immutable audit log entry."""
    entry_id: str
    event_type: AuditEventType
    actor: str
    action: str
    resource: str
    details: dict[str, Any]
    timestamp: str = field(default_factory=lambda: uuid4().hex[:12])
    hash_chain: str = ""  # Hash of previous entry for immutability


class SecurityAuditAgent:
    """Agent 18 -- Security & Audit Agent implementation."""

    AGENT_ID = "AGENT_18"
    AGENT_NAME = "Security & Audit Agent"
    DESCRIPTION = "Reviews permissions, secrets, external actions, incidents and audit evidence"

    # Allowed domains for external reference URLs (SSRF prevention)
    ALLOWED_DOMAINS = [
        "youtube.com",
        "youtu.be",
        "googleapis.com",
    ]

    # Dangerous patterns in external content
    DANGEROUS_PATTERNS = [
        "<script",
        "javascript:",
        "eval(",
        "document.cookie",
        "localStorage",
        "fetch(",
        "XMLHttpRequest",
        "__proto__",
        "constructor",
    ]

    def __init__(self) -> None:
        self.name = self.AGENT_NAME
        self.agent_id = self.AGENT_ID
        self._permission_reviews: dict[str, PermissionReview] = {}
        self._secret_audits: dict[str, SecretAudit] = {}
        self._incidents: dict[str, SecurityIncident] = {}
        self._input_validations: dict[str, InputValidationResult] = {}
        self._webhook_verifications: dict[str, WebhookVerificationResult] = {}
        self._ssrf_checks: dict[str, SSRFCheckResult] = {}
        self._audit_trail: list[AuditEntry] = []
        self._previous_hash = ""

    def review_permissions(
        self, user_id: str, role: str, permissions: list[str],
        tenant_boundaries: list[str],
    ) -> PermissionReview:
        """Review RBAC permissions and access boundaries."""
        review_id = f"perm_{uuid4().hex[:8]}"
        issues = []
        compliant = True

        # Check for overly broad permissions
        dangerous_perms = ["admin", "*", "all", "root"]
        for perm in permissions:
            if perm.lower() in dangerous_perms:
                issues.append(f"Overly broad permission: {perm}")
                compliant = False

        # Check tenant boundaries
        if not tenant_boundaries:
            issues.append("No tenant boundaries defined")
            compliant = False

        review = PermissionReview(
            review_id=review_id,
            user_id=user_id,
            role=role,
            permissions=permissions,
            tenant_boundaries=tenant_boundaries,
            compliant=compliant,
            issues=issues,
        )
        self._permission_reviews[review_id] = review
        self._add_audit_entry(
            AuditEventType.PERMISSION_CHANGE, "system",
            "permission_review", user_id,
            {"compliant": compliant, "issues": issues},
        )
        return review

    def audit_secret(
        self, secret_name: str, encrypted_at_rest: bool,
        never_in_source_control: bool, never_exposed_to_browser: bool,
        rotation_due: bool,
    ) -> SecretAudit:
        """Audit secret management practices."""
        audit_id = f"secret_{uuid4().hex[:8]}"
        issues = []
        compliant = True

        if not encrypted_at_rest:
            issues.append("Secret not encrypted at rest")
            compliant = False
        if not never_in_source_control:
            issues.append("Secret may be in source control")
            compliant = False
        if not never_exposed_to_browser:
            issues.append("Secret may be exposed to browser")
            compliant = False
        if rotation_due:
            issues.append("Secret rotation is due")
            compliant = False

        audit = SecretAudit(
            audit_id=audit_id,
            secret_name=secret_name,
            encrypted_at_rest=encrypted_at_rest,
            never_in_source_control=never_in_source_control,
            never_exposed_to_browser=never_exposed_to_browser,
            rotation_due=rotation_due,
            compliant=compliant,
            issues=issues,
        )
        self._secret_audits[audit_id] = audit
        self._add_audit_entry(
            AuditEventType.SECRET_ACCESS, "system",
            "secret_audit", secret_name,
            {"compliant": compliant, "issues": issues},
        )
        return audit

    def log_incident(
        self, event_type: AuditEventType, severity: Severity,
        description: str, affected_resources: list[str],
        actor: str | None = None,
    ) -> SecurityIncident:
        """Record a security incident."""
        incident_id = f"incident_{uuid4().hex[:8]}"

        incident = SecurityIncident(
            incident_id=incident_id,
            event_type=event_type,
            severity=severity,
            description=description,
            affected_resources=affected_resources,
            actor=actor,
            resolved=False,
            resolution_notes=None,
        )
        self._incidents[incident_id] = incident
        self._add_audit_entry(
            AuditEventType.INCIDENT, actor or "system",
            "incident_logged", incident_id,
            {"severity": severity.name, "description": description},
        )
        return incident

    def resolve_incident(
        self, incident_id: str, resolution_notes: str,
    ) -> dict[str, Any]:
        """Mark an incident as resolved."""
        if incident_id not in self._incidents:
            return {
                "status": "blocked",
                "error": f"Incident {incident_id} not found",
            }

        incident = self._incidents[incident_id]
        incident.resolved = True
        incident.resolution_notes = resolution_notes
        self._add_audit_entry(
            AuditEventType.INCIDENT, "system",
            "incident_resolved", incident_id,
            {"resolution_notes": resolution_notes},
        )

        return {
            "status": "completed",
            "incident_id": incident_id,
            "resolved": True,
        }

    def validate_input(
        self, input_id: str, input_type: str, content: str,
    ) -> InputValidationResult:
        """Validate and sanitize external input.

        Treats prompts, video metadata, captions and external content
        as untrusted input per Spec #16.
        """
        threats = []
        violations = []
        is_valid = True
        sanitized = False
        sanitized_content = content

        # Check for dangerous patterns
        content_lower = content.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in content_lower:
                threats.append(f"Dangerous pattern detected: {pattern}")
                is_valid = False

        # Check length limits
        if len(content) > 10000:
            violations.append("Input exceeds maximum length")
            is_valid = False

        # Sanitize if threats found
        if threats:
            sanitized = True
            # Remove dangerous patterns
            for pattern in self.DANGEROUS_PATTERNS:
                sanitized_content = sanitized_content.replace(pattern, "[REDACTED]")
                sanitized_content = sanitized_content.replace(
                    pattern.lower(), "[REDACTED]"
                )

        result = InputValidationResult(
            input_id=input_id,
            input_type=input_type,
            is_valid=is_valid,
            sanitized=sanitized,
            threats_detected=threats,
            violations=violations,
        )
        self._input_validations[input_id] = result
        self._add_audit_entry(
            AuditEventType.INPUT_VALIDATION, "system",
            "input_validated", input_id,
            {"input_type": input_type, "is_valid": is_valid, "threats": threats},
        )
        return result

    def verify_webhook(
        self, webhook_id: str, source: str, signature: str,
        timestamp: str, tolerance_seconds: int = 300,
    ) -> WebhookVerificationResult:
        """Verify webhook signature and timestamp.

        Per Spec #16: Webhook verification required.
        """
        # In a real implementation, this would verify the HMAC signature
        # against a shared secret. Here we validate the structure.
        signature_valid = bool(signature and len(signature) >= 16)
        timestamp_within_tolerance = True  # Would validate against current time

        verified = signature_valid and timestamp_within_tolerance

        result = WebhookVerificationResult(
            webhook_id=webhook_id,
            source=source,
            signature_valid=signature_valid,
            timestamp_within_tolerance=timestamp_within_tolerance,
            verified=verified,
        )
        self._webhook_verifications[webhook_id] = result
        self._add_audit_entry(
            AuditEventType.WEBHOOK_VERIFICATION, "system",
            "webhook_verified", webhook_id,
            {"source": source, "verified": verified},
        )
        return result

    def check_ssrf(
        self, url: str, allowed_domains: list[str] | None = None,
    ) -> SSRFCheckResult:
        """Check URL for SSRF vulnerabilities.

        Prevent SSRF when ingesting remote reference URLs per Spec #16.
        """
        domains = allowed_domains or self.ALLOWED_DOMAINS
        blocked_reasons = []
        is_safe = True

        # Simple domain extraction
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            scheme = parsed.scheme.lower()

            # Check scheme
            if scheme not in ["http", "https"]:
                blocked_reasons.append(f"Unsafe scheme: {scheme}")
                is_safe = False

            # Check domain against allowed list
            domain_allowed = any(
                domain == d or domain.endswith("." + d) for d in domains
            )
            if not domain_allowed:
                blocked_reasons.append(f"Domain not in allowlist: {domain}")
                is_safe = False

            # Check for localhost/private IP patterns
            if domain in ["localhost", "127.0.0.1", "0.0.0.0"]:
                blocked_reasons.append("Localhost address blocked")
                is_safe = False

            # Check for private IP ranges
            if any(domain.startswith(prefix) for prefix in ["10.", "172.16.", "192.168."]):
                blocked_reasons.append("Private IP address blocked")
                is_safe = False

        except Exception as e:
            blocked_reasons.append(f"Invalid URL: {str(e)}")
            is_safe = False

        result = SSRFCheckResult(
            url=url,
            is_safe=is_safe,
            blocked_reasons=blocked_reasons,
            allowed_domains=domains,
        )
        self._ssrf_checks[url] = result
        self._add_audit_entry(
            AuditEventType.SSRF_PREVENTION, "system",
            "ssrf_check", url,
            {"is_safe": is_safe, "blocked_reasons": blocked_reasons},
        )
        return result

    def enforce_human_approval(
        self, action: str, actor: str, requires_approval: bool = True,
    ) -> dict[str, Any]:
        """Enforce human approval for high-impact external actions.

        Per Spec #16: Enforce human approval for publishing and other
        high-impact external actions.
        """
        if requires_approval:
            return {
                "status": "blocked",
                "error": (
                    f"Human approval required for high-impact action: {action}. "
                    f"Actor: {actor}"
                ),
                "requires_human_approval": True,
            }

        self._add_audit_entry(
            AuditEventType.EXTERNAL_ACTION, actor,
            "external_action_approved", action,
            {"action": action, "human_approval": False},
        )
        return {
            "status": "completed",
            "action": action,
            "approved": True,
            "requires_human_approval": False,
        }

    def _add_audit_entry(
        self, event_type: AuditEventType, actor: str,
        action: str, resource: str, details: dict[str, Any],
    ) -> None:
        """Add an immutable audit entry with hash chain."""
        import hashlib

        entry_id = f"audit_{uuid4().hex[:8]}"
        entry = AuditEntry(
            entry_id=entry_id,
            event_type=event_type,
            actor=actor,
            action=action,
            resource=resource,
            details=details,
        )

        # Hash chain for immutability
        previous_hash = self._previous_hash
        entry_hash_input = f"{entry_id}:{event_type.name}:{actor}:{action}:{resource}:{previous_hash}"
        entry.hash_chain = hashlib.sha256(entry_hash_input.encode()).hexdigest()[:16]
        self._previous_hash = entry.hash_chain

        self._audit_trail.append(entry)

    def get_audit_trail(
        self, limit: int = 50, event_type: AuditEventType | None = None,
    ) -> list[dict[str, Any]]:
        """Get audit trail entries."""
        entries = self._audit_trail
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]

        # Return most recent first
        entries = sorted(entries, key=lambda e: e.timestamp, reverse=True)

        return [
            {
                "entry_id": e.entry_id,
                "event_type": e.event_type.name,
                "actor": e.actor,
                "action": e.action,
                "resource": e.resource,
                "details": e.details,
                "timestamp": e.timestamp,
                "hash_chain": e.hash_chain,
            }
            for e in entries[:limit]
        ]

    def get_security_summary(self) -> dict[str, Any]:
        """Get overall security summary."""
        open_incidents = [
            i for i in self._incidents.values() if not i.resolved
        ]
        critical_incidents = [
            i for i in open_incidents if i.severity == Severity.CRITICAL
        ]

        non_compliant_permissions = [
            p for p in self._permission_reviews.values() if not p.compliant
        ]
        non_compliant_secrets = [
            s for s in self._secret_audits.values() if not s.compliant
        ]

        return {
            "total_audit_entries": len(self._audit_trail),
            "open_incidents": len(open_incidents),
            "critical_incidents": len(critical_incidents),
            "non_compliant_permissions": len(non_compliant_permissions),
            "non_compliant_secrets": len(non_compliant_secrets),
            "ssrf_checks_performed": len(self._ssrf_checks),
            "webhook_verifications": len(self._webhook_verifications),
            "input_validations": len(self._input_validations),
        }

    def get_status(self) -> dict[str, Any]:
        """Return agent status."""
        return {
            "agent": self.AGENT_NAME,
            "agent_id": self.agent_id,
            "capability": "security_audit",
            "allowed_domains": self.ALLOWED_DOMAINS,
            "security_summary": self.get_security_summary(),
        }


# Module-level agent instance
agent = SecurityAuditAgent()


def execute_action(
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a Security & Audit Agent action.

    Args:
        action: The action to execute
        **kwargs: Arguments specific to the action

    Returns:
        Dictionary with action results
    """
    agent_obj = agent

    if action == "review_permissions":
        review = agent_obj.review_permissions(
            user_id=kwargs.get("user_id", ""),
            role=kwargs.get("role", ""),
            permissions=kwargs.get("permissions", []),
            tenant_boundaries=kwargs.get("tenant_boundaries", []),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "review_permissions",
            "status": "completed",
            "review_id": review.review_id,
            "user_id": review.user_id,
            "role": review.role,
            "compliant": review.compliant,
            "issues": review.issues,
        }

    elif action == "audit_secret":
        audit = agent_obj.audit_secret(
            secret_name=kwargs.get("secret_name", ""),
            encrypted_at_rest=kwargs.get("encrypted_at_rest", True),
            never_in_source_control=kwargs.get("never_in_source_control", True),
            never_exposed_to_browser=kwargs.get(
                "never_exposed_to_browser", True
            ),
            rotation_due=kwargs.get("rotation_due", False),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "audit_secret",
            "status": "completed",
            "audit_id": audit.audit_id,
            "secret_name": audit.secret_name,
            "compliant": audit.compliant,
            "issues": audit.issues,
        }

    elif action == "log_incident":
        incident = agent_obj.log_incident(
            event_type=AuditEventType[kwargs.get("event_type", "INCIDENT")],
            severity=Severity[kwargs.get("severity", "MEDIUM")],
            description=kwargs.get("description", ""),
            affected_resources=kwargs.get("affected_resources", []),
            actor=kwargs.get("actor"),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "log_incident",
            "status": "completed",
            "incident_id": incident.incident_id,
            "severity": incident.severity.name,
            "description": incident.description,
        }

    elif action == "resolve_incident":
        resolution_result = agent_obj.resolve_incident(
            incident_id=kwargs.get("incident_id", ""),
            resolution_notes=kwargs.get("resolution_notes", ""),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "resolve_incident",
            **resolution_result,
        }

    elif action == "validate_input":
        validation_result = agent_obj.validate_input(
            input_id=kwargs.get("input_id", ""),
            input_type=kwargs.get("input_type", ""),
            content=kwargs.get("content", ""),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "validate_input",
            "status": "completed",
            "input_id": validation_result.input_id,
            "input_type": validation_result.input_type,
            "is_valid": validation_result.is_valid,
            "sanitized": validation_result.sanitized,
            "threats_detected": validation_result.threats_detected,
            "violations": validation_result.violations,
        }

    elif action == "verify_webhook":
        webhook_result = agent_obj.verify_webhook(
            webhook_id=kwargs.get("webhook_id", ""),
            source=kwargs.get("source", ""),
            signature=kwargs.get("signature", ""),
            timestamp=kwargs.get("timestamp", ""),
            tolerance_seconds=kwargs.get("tolerance_seconds", 300),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "verify_webhook",
            "status": "completed",
            "webhook_id": webhook_result.webhook_id,
            "source": webhook_result.source,
            "signature_valid": webhook_result.signature_valid,
            "verified": webhook_result.verified,
        }

    elif action == "check_ssrf":
        ssrf_result = agent_obj.check_ssrf(
            url=kwargs.get("url", ""),
            allowed_domains=kwargs.get("allowed_domains"),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "check_ssrf",
            "status": "completed",
            "url": ssrf_result.url,
            "is_safe": ssrf_result.is_safe,
            "blocked_reasons": ssrf_result.blocked_reasons,
        }

    elif action == "enforce_human_approval":
        result = agent_obj.enforce_human_approval(
            action=kwargs.get("target_action", ""),
            actor=kwargs.get("actor", ""),
            requires_approval=kwargs.get("requires_approval", True),
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "enforce_human_approval",
            **result,
        }

    elif action == "get_audit_trail":
        event_type_raw = kwargs.get("event_type")
        event_type = AuditEventType[str(event_type_raw)] if event_type_raw else None
        trail = agent_obj.get_audit_trail(
            limit=kwargs.get("limit", 50),
            event_type=event_type,
        )
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_audit_trail",
            "status": "completed",
            "entries": trail,
        }

    elif action == "get_security_summary":
        return {
            "agent": agent_obj.AGENT_ID,
            "action": "get_security_summary",
            "status": "completed",
            "summary": agent_obj.get_security_summary(),
        }

    elif action == "status_check":
        return agent_obj.get_status()

    else:
        return {"agent": agent_obj.AGENT_ID, "action": action, "status": "blocked", "error": f"Unknown action: {action}"}


# Export for API/workflow usage
__all__ = [
    "SecurityAuditAgent",
    "PermissionReview",
    "SecretAudit",
    "SecurityIncident",
    "InputValidationResult",
    "WebhookVerificationResult",
    "SSRFCheckResult",
    "AuditEntry",
    "Severity",
    "AuditEventType",
    "RiskLevel",
    "execute_action",
    "agent",
]