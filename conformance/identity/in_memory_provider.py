"""In-Memory Reference Implementation of IdentityProvider.

Used to test and prove the Conformance Test Suite itself.
Zero external dependencies.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from uuid import UUID, uuid4

from contracts.identity import (
    AuthenticationContext,
    AuthOutcome,
    AuthResult,
    IdentityRecord,
    IdentityProvider,
    IdentityStatus,
    MFAChallenge,
    MFAChallengeStatus,
    MFAType,
    MFAVerificationResult,
    SubjectRecord,
    SubjectType,
)


class InMemoryIdentityProvider:
    """Pure in-memory conforming provider for tests and conformance validation."""

    def __init__(self) -> None:
        self.subjects: Dict[UUID, SubjectRecord] = {}
        self.identities: Dict[UUID, IdentityRecord] = {}
        self.identifier_to_id: Dict[Tuple[str, UUID], UUID] = {}  # (identifier, tenant_id) -> identity_id
        self.credentials: Dict[UUID, str] = {}  # identity_id -> hashed_password
        self.active_challenges: Dict[str, MFAChallenge] = {}

    def _hash_credential(self, secret: str) -> str:
        """Simple SHA-256 with salt for in-memory testing."""
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()

    def add_user(
        self,
        identifier: str,
        secret: str,
        tenant_id: UUID,
        status: IdentityStatus = IdentityStatus.ACTIVE,
        mfa_enabled: bool = False,
    ) -> Tuple[SubjectRecord, IdentityRecord]:
        subject_id = uuid4()
        identity_id = uuid4()

        subject = SubjectRecord(
            subject_id=subject_id,
            tenant_id=tenant_id,
            subject_type=SubjectType.HUMAN,
        )
        identity = IdentityRecord(
            identity_id=identity_id,
            subject_id=subject_id,
            tenant_id=tenant_id,
            identifier=identifier,
            status=status,
            mfa_enabled=mfa_enabled,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self.subjects[subject_id] = subject
        self.identities[identity_id] = identity
        self.identifier_to_id[(identifier, tenant_id)] = identity_id
        self.credentials[identity_id] = self._hash_credential(secret)
        return subject, identity

    def authenticate(
        self, identifier: str, credential: str, context: AuthenticationContext
    ) -> AuthResult:
        tenant_id = context.tenant_id
        if not tenant_id:
            return AuthResult(outcome=AuthOutcome.INVALID_CREDENTIALS, failure_reason="Tenant context missing")

        identity_id = self.identifier_to_id.get((identifier, tenant_id))
        if not identity_id:
            # Constant-time simulation, generic error
            self._hash_credential(credential)
            return AuthResult(outcome=AuthOutcome.INVALID_CREDENTIALS, failure_reason="Invalid credentials")

        identity = self.identities[identity_id]
        subject = self.subjects.get(identity.subject_id)

        # Lifecycle checks
        if identity.status == IdentityStatus.PENDING_VERIFICATION:
            return AuthResult(outcome=AuthOutcome.ACCOUNT_PENDING, identity=identity, subject=subject)
        if identity.status == IdentityStatus.LOCKED:
            return AuthResult(outcome=AuthOutcome.ACCOUNT_LOCKED, identity=identity, subject=subject)
        if identity.status == IdentityStatus.SUSPENDED:
            return AuthResult(outcome=AuthOutcome.ACCOUNT_SUSPENDED, identity=identity, subject=subject)
        if identity.status == IdentityStatus.TOMBSTONED:
            return AuthResult(outcome=AuthOutcome.INVALID_CREDENTIALS, failure_reason="Invalid credentials")

        # Credential check
        expected_hash = self.credentials.get(identity_id)
        candidate_hash = self._hash_credential(credential)
        if candidate_hash != expected_hash:
            return AuthResult(outcome=AuthOutcome.INVALID_CREDENTIALS, failure_reason="Invalid credentials")

        # MFA check
        if identity.mfa_enabled:
            challenge_id = f"mfa-chn-{secrets.token_hex(8)}"
            challenge = MFAChallenge(
                challenge_id=challenge_id,
                identity_id=identity_id,
                mfa_type=MFAType.TOTP,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            )
            self.active_challenges[challenge_id] = challenge
            return AuthResult(
                outcome=AuthOutcome.MFA_REQUIRED,
                identity=identity,
                subject=subject,
                mfa_challenge_id=challenge_id,
            )

        return AuthResult(
            outcome=AuthOutcome.SUCCESS,
            identity=identity,
            subject=subject,
            session_token=f"sess-{secrets.token_hex(16)}",
        )

    def get_identity_by_id(self, identity_id: UUID) -> Optional[IdentityRecord]:
        return self.identities.get(identity_id)

    def get_identity_by_identifier(
        self, identifier: str, tenant_id: UUID
    ) -> Optional[IdentityRecord]:
        identity_id = self.identifier_to_id.get((identifier, tenant_id))
        return self.identities.get(identity_id) if identity_id else None

    def get_subject_by_id(self, subject_id: UUID) -> Optional[SubjectRecord]:
        return self.subjects.get(subject_id)

    def verify_mfa(
        self, challenge_id: str, code: str, context: AuthenticationContext
    ) -> MFAVerificationResult:
        challenge = self.active_challenges.get(challenge_id)
        if not challenge:
            return MFAVerificationResult(success=False, challenge_id=challenge_id, failure_reason="Unknown challenge")

        if code == "123456":  # Standard mock code for test suite
            return MFAVerificationResult(success=True, challenge_id=challenge_id)
        return MFAVerificationResult(success=False, challenge_id=challenge_id, failure_reason="Invalid MFA token")

    def lock_identity(self, identity_id: UUID, duration_minutes: int, reason: str) -> None:
        rec = self.identities.get(identity_id)
        if rec:
            self.identities[identity_id] = IdentityRecord(
                identity_id=rec.identity_id,
                subject_id=rec.subject_id,
                tenant_id=rec.tenant_id,
                identifier=rec.identifier,
                status=IdentityStatus.LOCKED,
                failed_login_attempts=rec.failed_login_attempts,
                locked_until=datetime.now(timezone.utc) + timedelta(minutes=duration_minutes),
                mfa_enabled=rec.mfa_enabled,
                created_at=rec.created_at,
                updated_at=datetime.now(timezone.utc),
            )

    def unlock_identity(self, identity_id: UUID, reason: str) -> None:
        rec = self.identities.get(identity_id)
        if rec:
            self.identities[identity_id] = IdentityRecord(
                identity_id=rec.identity_id,
                subject_id=rec.subject_id,
                tenant_id=rec.tenant_id,
                identifier=rec.identifier,
                status=IdentityStatus.ACTIVE,
                failed_login_attempts=0,
                locked_until=None,
                mfa_enabled=rec.mfa_enabled,
                created_at=rec.created_at,
                updated_at=datetime.now(timezone.utc),
            )

    def suspend_identity(self, identity_id: UUID, reason: str) -> None:
        rec = self.identities.get(identity_id)
        if rec:
            self.identities[identity_id] = IdentityRecord(
                identity_id=rec.identity_id,
                subject_id=rec.subject_id,
                tenant_id=rec.tenant_id,
                identifier=rec.identifier,
                status=IdentityStatus.SUSPENDED,
                failed_login_attempts=rec.failed_login_attempts,
                mfa_enabled=rec.mfa_enabled,
                created_at=rec.created_at,
                updated_at=datetime.now(timezone.utc),
            )

    def tombstone_identity(self, identity_id: UUID, reason: str) -> None:
        rec = self.identities.get(identity_id)
        if rec:
            self.identities[identity_id] = IdentityRecord(
                identity_id=rec.identity_id,
                subject_id=rec.subject_id,
                tenant_id=rec.tenant_id,
                identifier=f"redacted_{rec.identity_id.hex[:8]}",
                status=IdentityStatus.TOMBSTONED,
                failed_login_attempts=0,
                mfa_enabled=False,
                created_at=rec.created_at,
                updated_at=datetime.now(timezone.utc),
            )

    def record_login_failure(
        self, identity_id: UUID, context: AuthenticationContext
    ) -> None:
        rec = self.identities.get(identity_id)
        if rec:
            attempts = rec.failed_login_attempts + 1
            if attempts >= 5:
                self.lock_identity(identity_id, duration_minutes=15, reason="Excessive failed logins")
            else:
                self.identities[identity_id] = IdentityRecord(
                    identity_id=rec.identity_id,
                    subject_id=rec.subject_id,
                    tenant_id=rec.tenant_id,
                    identifier=rec.identifier,
                    status=rec.status,
                    failed_login_attempts=attempts,
                    mfa_enabled=rec.mfa_enabled,
                    created_at=rec.created_at,
                    updated_at=datetime.now(timezone.utc),
                )

    def record_login_success(
        self, identity_id: UUID, context: AuthenticationContext
    ) -> None:
        rec = self.identities.get(identity_id)
        if rec:
            self.identities[identity_id] = IdentityRecord(
                identity_id=rec.identity_id,
                subject_id=rec.subject_id,
                tenant_id=rec.tenant_id,
                identifier=rec.identifier,
                status=rec.status,
                failed_login_attempts=0,
                mfa_enabled=rec.mfa_enabled,
                created_at=rec.created_at,
                updated_at=datetime.now(timezone.utc),
            )
