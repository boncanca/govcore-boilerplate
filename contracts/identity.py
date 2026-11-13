"""GovCore Identity & Authentication Contracts.

Normative Specification Authority:
    - Chapter 1: Core Domain Vocabulary (spec/v1.0/01-vocabulary.md)
    - Chapter 2: Identity, Credentials & Authentication (spec/v1.0/02-identity-and-auth.md)

Architectural Boundary:
    Pure Python interfaces and types. Zero framework or ORM dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Optional, Protocol, Sequence, Tuple, runtime_checkable
from uuid import UUID


class SubjectType(str, Enum):
    """Classification of the authenticated subject entity."""
    HUMAN = "HUMAN"
    SERVICE = "SERVICE"


class IdentityStatus(str, Enum):
    """Deterministic lifecycle state of an IdentityRecord.
    
    Adheres strictly to the state machine defined in spec/v1.0/02-identity-and-auth.md Section 2.
    """
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    SUSPENDED = "SUSPENDED"
    TOMBSTONED = "TOMBSTONED"


class AuthOutcome(str, Enum):
    """Result of an authentication attempt evaluated against credential and lifecycle rules."""
    SUCCESS = "SUCCESS"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_SUSPENDED = "ACCOUNT_SUSPENDED"
    ACCOUNT_PENDING = "ACCOUNT_PENDING"
    MFA_REQUIRED = "MFA_REQUIRED"
    PASSWORD_EXPIRED = "PASSWORD_EXPIRED"


class MFAType(str, Enum):
    """Supported multi-factor authentication methods."""
    TOTP = "TOTP"
    WEBAUTHN = "WEBAUTHN"
    RECOVERY_CODE = "RECOVERY_CODE"


class MFAChallengeStatus(str, Enum):
    """Current state of an active MFA challenge step."""
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class SubjectRecord:
    """Canonical Subject representing the permanent identity entity."""
    subject_id: UUID
    tenant_id: Optional[UUID]
    subject_type: SubjectType = SubjectType.HUMAN
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def canonical_urn(self) -> str:
        """Return the canonical URN for this Subject per spec Chapter 1."""
        scope = str(self.tenant_id) if self.tenant_id else "global"
        return f"urn:govcore:subject:{scope}:{self.subject_id}"


@dataclass(frozen=True)
class IdentityRecord:
    """The authentication and credential profile bound to a Subject."""
    identity_id: UUID
    subject_id: UUID
    tenant_id: UUID
    identifier: str
    status: IdentityStatus
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    mfa_enabled: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def is_operational(self) -> bool:
        """Return True if the identity is active and eligible to authenticate."""
        return self.status == IdentityStatus.ACTIVE


@dataclass(frozen=True)
class AuthenticationContext:
    """Contextual metadata accompanying an authentication request."""
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    tenant_id: Optional[UUID] = None
    correlation_id: Optional[str] = None


@dataclass(frozen=True)
class AuthResult:
    """Deterministic result of an authentication operation."""
    outcome: AuthOutcome
    identity: Optional[IdentityRecord] = None
    subject: Optional[SubjectRecord] = None
    session_token: Optional[str] = None
    mfa_challenge_id: Optional[str] = None
    failure_reason: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.outcome == AuthOutcome.SUCCESS


@dataclass(frozen=True)
class MFAChallenge:
    """An outstanding multi-factor challenge requiring second-factor verification."""
    challenge_id: str
    identity_id: UUID
    mfa_type: MFAType
    expires_at: datetime
    status: MFAChallengeStatus = MFAChallengeStatus.PENDING


@dataclass(frozen=True)
class MFAVerificationResult:
    """Result of an MFA verification attempt."""
    success: bool
    challenge_id: str
    failure_reason: Optional[str] = None
    recovery_code_used: bool = False


@runtime_checkable
class CredentialVerifier(Protocol):
    """Port for password hashing and verification algorithms.
    
    Implementations MUST enforce Argon2id per spec Chapter 2 Section 3.
    """

    def verify_password(self, secret: str, stored_hash: str) -> bool:
        """Verify candidate secret against stored hash in constant time."""
        ...

    def hash_password(self, secret: str) -> str:
        """Compute memory-hard hash of the secret using Argon2id."""
        ...

    def needs_rehash(self, stored_hash: str) -> bool:
        """Determine whether the stored hash requires upgrade (e.g. legacy PBKDF2)."""
        ...


@runtime_checkable
class MFAService(Protocol):
    """Port for Multi-Factor Authentication operations (TOTP & Recovery Codes).
    
    Implementations MUST adhere to spec Chapter 2 Section 4.
    """

    def generate_totp_secret(self) -> str:
        """Generate a cryptographically secure random base32 TOTP seed."""
        ...

    def verify_totp(self, secret: str, code: str, allowed_drift_windows: int = 1) -> bool:
        """Verify an RFC 6238 TOTP code against a secret within the allowed drift window."""
        ...

    def generate_recovery_codes(self, count: int = 10) -> Tuple[Sequence[str], Sequence[str]]:
        """Generate recovery codes returning a tuple of (plaintext_codes, hashed_codes)."""
        ...

    def verify_recovery_code(
        self, candidate_code: str, stored_hashes: Sequence[str]
    ) -> Tuple[bool, Optional[str]]:
        """Verify candidate recovery code against stored hashes.
        
        Returns:
            Tuple of (is_valid, matched_hash_to_invalidate).
        """
        ...


@runtime_checkable
class IdentityProvider(Protocol):
    """Primary programmatic port for Identity & Authentication operations.
    
    Adapters (Django, FastAPI, Frappe) implement this protocol to satisfy
    GovCore Specification Chapter 2.
    """

    def authenticate(
        self, identifier: str, credential: str, context: AuthenticationContext
    ) -> AuthResult:
        """Authenticate a candidate against an identifier and credential within the context.
        
        MUST enforce:
        - Constant-time verification
        - Lifecycle state checks (LOCKED, SUSPENDED, PENDING_VERIFICATION)
        - Brute-force failure count increment and lockout thresholding
        - Step-up MFA challenge issuance if MFA is enabled
        """
        ...

    def get_identity_by_id(self, identity_id: UUID) -> Optional[IdentityRecord]:
        """Retrieve an identity by its primary unique UUID."""
        ...

    def get_identity_by_identifier(
        self, identifier: str, tenant_id: UUID
    ) -> Optional[IdentityRecord]:
        """Retrieve an identity by human identifier scoped to a tenant."""
        ...

    def get_subject_by_id(self, subject_id: UUID) -> Optional[SubjectRecord]:
        """Retrieve a subject record by UUID."""
        ...

    def verify_mfa(
        self, challenge_id: str, code: str, context: AuthenticationContext
    ) -> MFAVerificationResult:
        """Complete an outstanding MFA challenge."""
        ...

    def lock_identity(self, identity_id: UUID, duration_minutes: int, reason: str) -> None:
        """Transition an identity to LOCKED status with an expiration timestamp."""
        ...

    def unlock_identity(self, identity_id: UUID, reason: str) -> None:
        """Restore a LOCKED identity back to ACTIVE status."""
        ...

    def suspend_identity(self, identity_id: UUID, reason: str) -> None:
        """Transition an identity to SUSPENDED status and invalidate all active sessions."""
        ...

    def tombstone_identity(self, identity_id: UUID, reason: str) -> None:
        """Transition an identity to TOMBSTONED status and redact PII while preserving UUID."""
        ...

    def record_login_failure(
        self, identity_id: UUID, context: AuthenticationContext
    ) -> None:
        """Increment failure counter and enforce lockout if threshold is exceeded."""
        ...

    def record_login_success(
        self, identity_id: UUID, context: AuthenticationContext
    ) -> None:
        """Reset failure counter and update last login timestamps."""
        ...
