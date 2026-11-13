"""GovCore Access Control & Authorization Contracts.

Normative Specification Authority:
    - Chapter 1: Core Domain Vocabulary (spec/v1.0/01-vocabulary.md)
    - Chapter 4: Access Control & Authorization (spec/v1.0/04-authorization.md)

Architectural Boundary:
    Pure Python interfaces, protocols, and standard decision records.
    Zero framework, ORM, or HTTP dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Optional, Protocol, Sequence, runtime_checkable
from uuid import UUID


class Decision(str, Enum):
    """Access control evaluation outcome."""
    ALLOW = "ALLOW"
    DENY = "DENY"


class ActionType(str, Enum):
    """Standard public-sector governance actions."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    APPROVE = "APPROVE"
    SIGN = "SIGN"
    EXPORT = "EXPORT"


class SecurityClassification(str, Enum):
    """Information security classification level."""
    PUBLIC = "PUBLIC"
    OFFICIAL = "OFFICIAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"

    @property
    def level(self) -> int:
        """Numeric rank for clearance comparisons."""
        ranks = {
            "PUBLIC": 0,
            "OFFICIAL": 1,
            "CONFIDENTIAL": 2,
            "RESTRICTED": 3,
        }
        return ranks[self.value]


class AuthorizationError(Exception):
    """Base exception for authorization evaluation failures."""
    pass


class AccessDeniedError(AuthorizationError):
    """Raised when an operation is denied by the policy engine."""

    def __init__(self, message: str, code: Optional[str] = None, policy_id: Optional[str] = None) -> None:
        super().__init__(message)
        self.code = code
        self.policy_id = policy_id


@dataclass(frozen=True)
class ResourceTarget:
    """The target entity subjected to an access control check."""
    resource_id: str
    resource_type: str
    tenant_id: UUID
    classification: SecurityClassification = SecurityClassification.OFFICIAL
    attributes: Mapping[str, Any] = field(default_factory=dict)

    @property
    def canonical_urn(self) -> str:
        """Return canonical URN for this Resource per spec Chapter 1."""
        return f"urn:govcore:resource:{self.tenant_id}:{self.resource_type}:{self.resource_id}"


@dataclass(frozen=True)
class Actor:
    """The runtime operational entity attempting an action."""
    subject_id: UUID
    tenant_id: UUID
    roles: Sequence[str] = field(default_factory=list)
    clearance: SecurityClassification = SecurityClassification.OFFICIAL
    mfa_verified: bool = False
    session_id: Optional[str] = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    @property
    def canonical_urn(self) -> str:
        """Return canonical URN for this Actor execution context."""
        return f"urn:govcore:actor:{self.tenant_id}:{self.subject_id}"

    def has_role(self, role: str) -> bool:
        """Check if actor holds a specific role."""
        return role in self.roles


@dataclass(frozen=True)
class EvaluationContext:
    """Contextual and environmental metadata accompanying an access request."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    client_ip: Optional[str] = None
    environment_attributes: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AccessDecision:
    """Deterministic result of an authorization evaluation."""
    decision: Decision
    reason: Optional[str] = None
    code: Optional[str] = None
    matched_policy_id: Optional[str] = None

    @property
    def is_allowed(self) -> bool:
        return self.decision == Decision.ALLOW

    @classmethod
    def allow(cls, policy_id: Optional[str] = None, reason: str = "Permitted by policy") -> AccessDecision:
        return cls(decision=Decision.ALLOW, matched_policy_id=policy_id, reason=reason)

    @classmethod
    def deny(cls, reason: str = "Denied by policy", code: Optional[str] = None, policy_id: Optional[str] = None) -> AccessDecision:
        return cls(decision=Decision.DENY, reason=reason, code=code, matched_policy_id=policy_id)


@runtime_checkable
class PolicyEngine(Protocol):
    """Primary programmatic port for evaluating authorization decisions.
    
    Implementations MUST enforce fail-closed evaluation and tenant isolation.
    """

    def evaluate(
        self,
        actor: Actor,
        action: str,
        resource: ResourceTarget,
        context: Optional[EvaluationContext] = None,
    ) -> AccessDecision:
        """Evaluate whether the actor is permitted to perform the action on the resource."""
        ...

    def enforce(
        self,
        actor: Actor,
        action: str,
        resource: ResourceTarget,
        context: Optional[EvaluationContext] = None,
    ) -> None:
        """Evaluate access and raise AccessDeniedError if not permitted."""
        ...
