"""Base Conformance Test Suite for Authorization & Policy Engines.

Normative Specification Authority:
    - Chapter 1: Core Domain Vocabulary (spec/v1.0/01-vocabulary.md)
    - Chapter 4: Access Control & Authorization (spec/v1.0/04-authorization.md)

Any adapter (Django, FastAPI, Frappe) MUST pass this test suite to claim
GovCore Authorization Conformance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID, uuid4

from contracts.authorization import (
    AccessDecision,
    AccessDeniedError,
    ActionType,
    Actor,
    Decision,
    PolicyEngine,
    ResourceTarget,
    SecurityClassification,
)


class BaseAuthorizationConformanceTestSuite(ABC):
    """Abstract conformance verification mixin for PolicyEngine implementations."""

    @abstractmethod
    def create_policy_engine(self) -> PolicyEngine:
        """Return the PolicyEngine instance under test."""
        raise NotImplementedError

    @abstractmethod
    def register_role_permission(self, role: str, resource_type: str, action: str) -> None:
        """Register a permitted (role, resource_type, action) tuple in the test engine."""
        raise NotImplementedError

    def setUp(self) -> None:
        super().setUp()
        self.engine = self.create_policy_engine()
        self.tenant_id = uuid4()

    def test_engine_satisfies_protocol(self) -> None:
        """Invariant: Policy engine must satisfy PolicyEngine protocol."""
        self.assertIsInstance(
            self.engine,
            PolicyEngine,
            "Candidate fails structural conformance for PolicyEngine.",
        )

    def test_canonical_urns(self) -> None:
        """Chapter 1: Resource and Actor canonical URN formatting."""
        subject_id = uuid4()
        actor = Actor(subject_id=subject_id, tenant_id=self.tenant_id)
        self.assertEqual(actor.canonical_urn, f"urn:govcore:actor:{self.tenant_id}:{subject_id}")

        resource = ResourceTarget(
            resource_id="doc-991",
            resource_type="permit_application",
            tenant_id=self.tenant_id,
        )
        self.assertEqual(
            resource.canonical_urn,
            f"urn:govcore:resource:{self.tenant_id}:permit_application:doc-991",
        )

    def test_fail_closed_default_invariant(self) -> None:
        """Chapter 4 Section 3.1: Policy evaluation must default to DENY."""
        actor = Actor(
            subject_id=uuid4(),
            tenant_id=self.tenant_id,
            roles=["Citizen"],
        )
        resource = ResourceTarget(
            resource_id="app-1",
            resource_type="unknown_resource",
            tenant_id=self.tenant_id,
        )

        decision = self.engine.evaluate(actor, "unknown_action", resource)
        self.assertEqual(decision.decision, Decision.DENY)
        self.assertFalse(decision.is_allowed)

    def test_tenant_boundary_isolation_invariant(self) -> None:
        """Chapter 4 Section 3.2: Cross-tenant access must be rejected with CROSS_TENANT_VIOLATION."""
        other_tenant_id = uuid4()
        self.register_role_permission("Officer", "tax_record", "read")

        actor = Actor(
            subject_id=uuid4(),
            tenant_id=self.tenant_id,
            roles=["Officer"],
        )
        other_resource = ResourceTarget(
            resource_id="tax-123",
            resource_type="tax_record",
            tenant_id=other_tenant_id,
        )

        decision = self.engine.evaluate(actor, "read", other_resource)
        self.assertEqual(decision.decision, Decision.DENY)
        self.assertEqual(decision.code, "CROSS_TENANT_VIOLATION")

    def test_security_classification_clearance_invariant(self) -> None:
        """Chapter 4 Section 3.3: Resource classification exceeding actor clearance must yield DENY."""
        self.register_role_permission("Officer", "classified_dossier", "read")

        actor = Actor(
            subject_id=uuid4(),
            tenant_id=self.tenant_id,
            roles=["Officer"],
            clearance=SecurityClassification.OFFICIAL,
        )
        restricted_resource = ResourceTarget(
            resource_id="dossier-007",
            resource_type="classified_dossier",
            tenant_id=self.tenant_id,
            classification=SecurityClassification.RESTRICTED,
        )

        decision = self.engine.evaluate(actor, "read", restricted_resource)
        self.assertEqual(decision.decision, Decision.DENY)
        self.assertEqual(decision.code, "INSUFFICIENT_CLEARANCE")

    def test_mfa_step_up_invariant(self) -> None:
        """Chapter 4 Section 3.4: Privileged actions requiring MFA must yield MFA_STEP_UP_REQUIRED if unverified."""
        self.register_role_permission("TenantAdmin", "citizen_registry", ActionType.EXPORT.value)

        actor_without_mfa = Actor(
            subject_id=uuid4(),
            tenant_id=self.tenant_id,
            roles=["TenantAdmin"],
            clearance=SecurityClassification.RESTRICTED,
            mfa_verified=False,
        )
        resource = ResourceTarget(
            resource_id="citizens_all",
            resource_type="citizen_registry",
            tenant_id=self.tenant_id,
            classification=SecurityClassification.OFFICIAL,
        )

        decision = self.engine.evaluate(actor_without_mfa, ActionType.EXPORT.value, resource)
        self.assertEqual(decision.decision, Decision.DENY)
        self.assertEqual(decision.code, "MFA_STEP_UP_REQUIRED")

        # When MFA is verified, export is granted
        actor_with_mfa = Actor(
            subject_id=actor_without_mfa.subject_id,
            tenant_id=self.tenant_id,
            roles=["TenantAdmin"],
            clearance=SecurityClassification.RESTRICTED,
            mfa_verified=True,
        )
        decision_mfa = self.engine.evaluate(actor_with_mfa, ActionType.EXPORT.value, resource)
        self.assertEqual(decision_mfa.decision, Decision.ALLOW)

    def test_enforce_raises_access_denied_error(self) -> None:
        """PolicyEngine.enforce() must raise AccessDeniedError on DENY and pass silently on ALLOW."""
        actor = Actor(subject_id=uuid4(), tenant_id=self.tenant_id, roles=["Citizen"])
        resource = ResourceTarget(resource_id="res-1", resource_type="private_file", tenant_id=self.tenant_id)

        with self.assertRaises(AccessDeniedError):
            self.engine.enforce(actor, "delete", resource)

        # Register permission and verify silent pass
        self.register_role_permission("Citizen", "private_file", "delete")
        try:
            self.engine.enforce(actor, "delete", resource)
        except AccessDeniedError:
            self.fail("enforce() unexpectedly raised AccessDeniedError for permitted action.")
