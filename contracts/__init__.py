"""GovCore Programmatic Contracts.

This package defines the pure-Python interfaces, protocols, and data structures
that establish the programmatic boundary for GovCore-compliant implementations.

Architectural Rule:
    No contract in this package may import Django, FastAPI, Flask, Frappe,
    SQLAlchemy, ORM-specific models, HTTP framework requests, or framework-specific
    exceptions. All contracts rely strictly on the Python standard library typing
    and built-in modules.
"""

from contracts.authorization import (
    AccessDecision,
    AccessDeniedError,
    ActionType,
    Actor,
    AuthorizationError,
    Decision,
    EvaluationContext,
    PolicyEngine,
    ResourceTarget,
    SecurityClassification,
)
from contracts.identity import (
    AuthenticationContext,
    AuthOutcome,
    AuthResult,
    CredentialVerifier,
    IdentityRecord,
    IdentityProvider,
    IdentityStatus,
    MFAChallenge,
    MFAChallengeStatus,
    MFAService,
    MFAType,
    MFAVerificationResult,
    SubjectRecord,
    SubjectType,
)
from contracts.tenancy import (
    CrossTenantAccessError,
    DefaultTenantContextManager,
    TenantContext,
    TenantContextManager,
    TenantContextMissingError,
    TenantError,
    TenantInactiveError,
    TenantIsolationModel,
    TenantNotFoundError,
    TenantRecord,
    TenantResolver,
    TenantStatus,
    TenantStore,
)

__all__ = [
    # Identity
    "AuthenticationContext",
    "AuthOutcome",
    "AuthResult",
    "CredentialVerifier",
    "IdentityRecord",
    "IdentityProvider",
    "IdentityStatus",
    "MFAChallenge",
    "MFAChallengeStatus",
    "MFAService",
    "MFAType",
    "MFAVerificationResult",
    "SubjectRecord",
    "SubjectType",
    # Tenancy
    "CrossTenantAccessError",
    "DefaultTenantContextManager",
    "TenantContext",
    "TenantContextManager",
    "TenantContextMissingError",
    "TenantError",
    "TenantInactiveError",
    "TenantIsolationModel",
    "TenantNotFoundError",
    "TenantRecord",
    "TenantResolver",
    "TenantStatus",
    "TenantStore",
    # Authorization
    "AccessDecision",
    "AccessDeniedError",
    "ActionType",
    "Actor",
    "AuthorizationError",
    "Decision",
    "EvaluationContext",
    "PolicyEngine",
    "ResourceTarget",
    "SecurityClassification",
]
