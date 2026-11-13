"""Verification of Tenancy Conformance Suite using in-memory implementations."""

import unittest

from conformance.tenancy.in_memory_resolver import InMemoryTenantResolver, InMemoryTenantStore
from conformance.tenancy.suite import BaseTenancyConformanceTestSuite
from contracts.tenancy import (
    DefaultTenantContextManager,
    TenantContextManager,
    TenantIsolationModel,
    TenantRecord,
    TenantResolver,
    TenantStatus,
)


class TestInMemoryTenancyConformance(BaseTenancyConformanceTestSuite, unittest.TestCase):
    """Executes the complete BaseTenancyConformanceTestSuite against reference implementation."""

    def create_context_manager(self) -> TenantContextManager:
        return DefaultTenantContextManager()

    def create_resolver(self) -> TenantResolver:
        self.store = InMemoryTenantStore()
        return InMemoryTenantResolver(self.store)

    def seed_tenant(
        self,
        slug: str,
        name: str,
        status: TenantStatus = TenantStatus.ACTIVE,
        isolation_model: TenantIsolationModel = TenantIsolationModel.DISCRIMINATOR,
    ) -> TenantRecord:
        return self.store.add_tenant(slug=slug, name=name, status=status, isolation_model=isolation_model)


if __name__ == "__main__":
    unittest.main()
