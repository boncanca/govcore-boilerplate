"""Base Conformance Test Suite for Identity & Authentication Providers.

Normative Specification Authority:
    - Chapter 1: Core Domain Vocabulary (spec/v1.0/01-vocabulary.md)
    - Chapter 2: Identity, Credentials & Authentication (spec/v1.0/02-identity-and-auth.md)

Any adapter (Django, FastAPI, Frappe) MUST pass this test suite to claim
GovCore Identity Conformance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple
from uuid import UUID, uuid4

from contracts.identity import (
    AuthenticationContext,
    AuthOutcome,
    IdentityProvider,
    IdentityRecord,
    IdentityStatus,
    SubjectRecord,
)


class BaseIdentityConformanceTestSuite(ABC):
    """Abstract conformance verification suite for IdentityProvider implementations.
    
    Adapters mix this in with unittest.TestCase (or execute via pytest)
    and implement create_provider() and seed_subject_and_identity().
    """

    @abstractmethod
    def create_provider(self) -> IdentityProvider:
        """Factory method returning the IdentityProvider instance under test."""
        raise NotImplementedError

    @abstractmethod
    def seed_subject_and_identity(
        self,
        identifier: str,
        secret: str,
        status: IdentityStatus = IdentityStatus.ACTIVE,
        mfa_enabled: bool = False,
        tenant_id: UUID = None,
    ) -> Tuple[SubjectRecord, IdentityRecord]:
        """Seed a subject and identity in the underlying provider store."""
        raise NotImplementedError

    def setUp(self) -> None:
        super().setUp()
        self.provider = self.create_provider()
        self.tenant_id = uuid4()
        self.context = AuthenticationContext(
            client_ip="127.0.0.1",
            user_agent="GovCore-Conformance-Runner/1.0",
            tenant_id=self.tenant_id,
        )

    def test_provider_satisfies_protocol(self) -> None:
        """Invariant: Provider must be runtime-checkable as IdentityProvider."""
        self.assertIsInstance(
            self.provider,
            IdentityProvider,
            "Candidate provider fails structural conformance for IdentityProvider protocol.",
        )

    def test_canonical_urn_format(self) -> None:
        """Chapter 1: Subject canonical URN must match urn:govcore:subject:<scope>:<id>."""
        subject_id = uuid4()
        scoped_subject = SubjectRecord(subject_id=subject_id, tenant_id=self.tenant_id)
        expected_urn = f"urn:govcore:subject:{self.tenant_id}:{subject_id}"
        self.assertEqual(scoped_subject.canonical_urn, expected_urn)

        global_subject = SubjectRecord(subject_id=subject_id, tenant_id=None)
        self.assertEqual(
            global_subject.canonical_urn,
            f"urn:govcore:subject:global:{subject_id}",
        )

    def test_authenticate_active_identity_success(self) -> None:
        """Chapter 2: Active identity with valid credentials must authenticate successfully."""
        identifier = "officer.smith"
        secret = "CorrectHorseBatteryStaple#2026"
        self.seed_subject_and_identity(identifier, secret, status=IdentityStatus.ACTIVE, tenant_id=self.tenant_id)

        result = self.provider.authenticate(identifier, secret, self.context)
        self.assertEqual(result.outcome, AuthOutcome.SUCCESS)
        self.assertTrue(result.is_success)
        self.assertIsNotNone(result.identity)
        self.assertEqual(result.identity.identifier, identifier)

    def test_authenticate_invalid_credentials(self) -> None:
        """Chapter 2: Active identity with wrong credential must return INVALID_CREDENTIALS."""
        identifier = "officer.jones"
        self.seed_subject_and_identity(identifier, "ValidSecret#123", status=IdentityStatus.ACTIVE, tenant_id=self.tenant_id)

        result = self.provider.authenticate(identifier, "WrongPassword#999", self.context)
        self.assertEqual(result.outcome, AuthOutcome.INVALID_CREDENTIALS)
        self.assertFalse(result.is_success)

    def test_authenticate_non_disclosing_errors(self) -> None:
        """Chapter 2 Section 7: Authentication responses must not reveal account existence."""
        result_non_existent = self.provider.authenticate("non.existent.user", "AnyPassword#123", self.context)
        self.assertEqual(
            result_non_existent.outcome,
            AuthOutcome.INVALID_CREDENTIALS,
            "Non-existent users must return generic INVALID_CREDENTIALS to prevent enumeration.",
        )

    def test_authenticate_pending_verification(self) -> None:
        """Chapter 2 Section 2: PENDING_VERIFICATION identities must not authenticate."""
        identifier = "pending.citizen"
        secret = "SecretPass#2026"
        self.seed_subject_and_identity(
            identifier, secret, status=IdentityStatus.PENDING_VERIFICATION, tenant_id=self.tenant_id
        )

        result = self.provider.authenticate(identifier, secret, self.context)
        self.assertEqual(result.outcome, AuthOutcome.ACCOUNT_PENDING)
        self.assertFalse(result.is_success)

    def test_authenticate_locked_identity(self) -> None:
        """Chapter 2 Section 2: LOCKED identities must return ACCOUNT_LOCKED."""
        identifier = "locked.user"
        secret = "SecretPass#2026"
        self.seed_subject_and_identity(identifier, secret, status=IdentityStatus.LOCKED, tenant_id=self.tenant_id)

        result = self.provider.authenticate(identifier, secret, self.context)
        self.assertEqual(result.outcome, AuthOutcome.ACCOUNT_LOCKED)
        self.assertFalse(result.is_success)

    def test_authenticate_suspended_identity(self) -> None:
        """Chapter 2 Section 2: SUSPENDED identities must return ACCOUNT_SUSPENDED."""
        identifier = "suspended.user"
        secret = "SecretPass#2026"
        self.seed_subject_and_identity(identifier, secret, status=IdentityStatus.SUSPENDED, tenant_id=self.tenant_id)

        result = self.provider.authenticate(identifier, secret, self.context)
        self.assertEqual(result.outcome, AuthOutcome.ACCOUNT_SUSPENDED)
        self.assertFalse(result.is_success)

    def test_lock_and_unlock_lifecycle(self) -> None:
        """Chapter 2 Section 2: lock_identity and unlock_identity must transition state correctly."""
        identifier = "target.officer"
        _, identity = self.seed_subject_and_identity(identifier, "SecretPass#2026", status=IdentityStatus.ACTIVE, tenant_id=self.tenant_id)

        self.provider.lock_identity(identity.identity_id, duration_minutes=15, reason="Security audit test")
        locked_record = self.provider.get_identity_by_id(identity.identity_id)
        self.assertIsNotNone(locked_record)
        self.assertEqual(locked_record.status, IdentityStatus.LOCKED)

        self.provider.unlock_identity(identity.identity_id, reason="Admin manual clearance")
        unlocked_record = self.provider.get_identity_by_id(identity.identity_id)
        self.assertIsNotNone(unlocked_record)
        self.assertEqual(unlocked_record.status, IdentityStatus.ACTIVE)

    def test_mfa_challenge_issuance_and_verification(self) -> None:
        """Chapter 2 Section 4: Identities with MFA enabled must require challenge step."""
        identifier = "mfa.admin"
        secret = "AdminSecret#2026"
        self.seed_subject_and_identity(
            identifier, secret, status=IdentityStatus.ACTIVE, mfa_enabled=True, tenant_id=self.tenant_id
        )

        auth_result = self.provider.authenticate(identifier, secret, self.context)
        self.assertEqual(auth_result.outcome, AuthOutcome.MFA_REQUIRED)
        self.assertIsNotNone(auth_result.mfa_challenge_id)

        # Invalid challenge response fails
        verify_fail = self.provider.verify_mfa(auth_result.mfa_challenge_id, "000000", self.context)
        self.assertFalse(verify_fail.success)

        # Valid challenge response succeeds (assumes test provider accepts '123456' as valid test code)
        verify_success = self.provider.verify_mfa(auth_result.mfa_challenge_id, "123456", self.context)
        self.assertTrue(verify_success.success)
