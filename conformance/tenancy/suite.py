"""Base Conformance Test Suite for Tenancy & Sovereign Isolation.

Normative Specification Authority:
    - Chapter 1: Core Domain Vocabulary (spec/v1.0/01-vocabulary.md)
    - Chapter 3: Organization & Multi-Tenancy (spec/v1.0/03-tenancy.md)

Any adapter (Django, FastAPI, Frappe) MUST pass this test suite to claim
GovCore Tenancy Conformance.
"""

from __future__ import annotations

import unittest
from abc import ABC, abstractmethod
from uuid import UUID, uuid4

from contracts.tenancy import (
    TenantContext,
    TenantContextManager,
    TenantContextMissingError,
    TenantInactiveError,
    TenantIsolationModel,
    TenantRecord,
    TenantResolver,
    TenantStatus,
)


class BaseTenancyConformanceTestSuite(ABC):
    """Abstract conformance verification mixin for Tenancy implementations."""

    @abstractmethod
    def create_context_manager(self) -> TenantContextManager:
        """Return the TenantContextManager instance under test."""
        raise NotImplementedError

    @abstractmethod
    def create_resolver(self) -> TenantResolver:
        """Return the TenantResolver instance under test."""
        raise NotImplementedError

    @abstractmethod
    def seed_tenant(
        self,
        slug: str,
        name: str,
        status: TenantStatus = TenantStatus.ACTIVE,
        isolation_model: TenantIsolationModel = TenantIsolationModel.DISCRIMINATOR,
    ) -> TenantRecord:
        """Seed a tenant record into the test store."""
        raise NotImplementedError

    def setUp(self) -> None:
        super().setUp()
        self.context_manager = self.create_context_manager()
        self.resolver = self.create_resolver()

    def tearDown(self) -> None:
        self.context_manager.clear_context()
        super().tearDown()

    def test_manager_satisfies_protocol(self) -> None:
        """Invariant: Context manager must satisfy TenantContextManager protocol."""
        self.assertIsInstance(
            self.context_manager,
            TenantContextManager,
            "Candidate fails structural conformance for TenantContextManager.",
        )

    def test_resolver_satisfies_protocol(self) -> None:
        """Invariant: Resolver must satisfy TenantResolver protocol."""
        self.assertIsInstance(
            self.resolver,
            TenantResolver,
            "Candidate fails structural conformance for TenantResolver.",
        )

    def test_canonical_tenant_urn(self) -> None:
        """Chapter 1: Tenant canonical URN must match urn:govcore:tenant:<tenant_id>."""
        tenant_id = uuid4()
        tenant = TenantRecord(
            tenant_id=tenant_id,
            slug="min-health",
            name="Ministry of Health",
            status=TenantStatus.ACTIVE,
        )
        self.assertEqual(tenant.canonical_urn, f"urn:govcore:tenant:{tenant_id}")

    def test_require_tenant_raises_when_missing(self) -> None:
        """Chapter 3 Section 5: Unbound context must fail closed with TenantContextMissingError."""
        self.context_manager.clear_context()
        with self.assertRaises(TenantContextMissingError):
            self.context_manager.require_current_tenant()

    def test_bind_and_retrieve_active_tenant(self) -> None:
        """Chapter 3 Section 2: Active tenant must bind and resolve successfully."""
        tenant = self.seed_tenant("min-justice", "Ministry of Justice", status=TenantStatus.ACTIVE)
        ctx = TenantContext(tenant=tenant)
        self.context_manager.set_current_context(ctx)

        resolved = self.context_manager.require_current_tenant()
        self.assertEqual(resolved.tenant_id, tenant.tenant_id)
        self.assertEqual(resolved.slug, "min-justice")
        self.assertTrue(resolved.is_operational)

    def test_suspended_tenant_raises_tenant_inactive_error(self) -> None:
        """Chapter 3 Section 2: Non-active tenant must fail with TenantInactiveError."""
        suspended = self.seed_tenant("min-transport", "Ministry of Transport", status=TenantStatus.SUSPENDED)
        ctx = TenantContext(tenant=suspended)
        self.context_manager.set_current_context(ctx)

        with self.assertRaises(TenantInactiveError):
            self.context_manager.require_current_tenant()

    def test_context_scoping_restores_previous(self) -> None:
        """Chapter 3 Section 5: Context scoping must cleanly restore enclosing context upon exit."""
        t1 = self.seed_tenant("tenant-one", "Tenant One")
        t2 = self.seed_tenant("tenant-two", "Tenant Two")

        self.context_manager.set_current_context(TenantContext(tenant=t1))
        self.assertEqual(self.context_manager.require_current_tenant().slug, "tenant-one")

        # Nested scoped block
        if hasattr(self.context_manager, "scope_context"):
            with self.context_manager.scope_context(TenantContext(tenant=t2)):
                self.assertEqual(self.context_manager.require_current_tenant().slug, "tenant-two")

            # Must be restored to t1
            self.assertEqual(self.context_manager.require_current_tenant().slug, "tenant-one")

    def test_resolver_priority_host_over_header_and_claim(self) -> None:
        """Chapter 3 Section 4: Host header resolution takes precedence over Header and Claim."""
        host_tenant = self.seed_tenant("host-dept", "Host Dept")
        header_tenant = self.seed_tenant("header-dept", "Header Dept")

        resolved = self.resolver.resolve_tenant(
            host="host-dept.portal.gov",
            header_value=str(header_tenant.tenant_id),
            subject_tenant_id=uuid4(),
        )
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.slug, "host-dept")

    def test_resolver_fallback_to_header_when_host_unmatched(self) -> None:
        """Chapter 3 Section 4: Fallback to X-Tenant-ID header when host does not match."""
        header_tenant = self.seed_tenant("fallback-dept", "Fallback Dept")

        resolved = self.resolver.resolve_tenant(
            host="unknown.example.org",
            header_value=str(header_tenant.tenant_id),
        )
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.slug, "fallback-dept")
