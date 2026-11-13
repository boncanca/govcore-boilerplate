"""Verification of Conformance Test Suite using InMemoryIdentityProvider."""

import unittest
from typing import Tuple
from uuid import UUID

from conformance.identity.in_memory_provider import InMemoryIdentityProvider
from conformance.identity.suite import BaseIdentityConformanceTestSuite
from contracts.identity import IdentityProvider, IdentityRecord, IdentityStatus, SubjectRecord


class TestInMemoryIdentityConformance(BaseIdentityConformanceTestSuite, unittest.TestCase):
    """Executes the complete BaseIdentityConformanceTestSuite against the in-memory provider."""

    def create_provider(self) -> IdentityProvider:
        self.mem_provider = InMemoryIdentityProvider()
        return self.mem_provider

    def seed_subject_and_identity(
        self,
        identifier: str,
        secret: str,
        status: IdentityStatus = IdentityStatus.ACTIVE,
        mfa_enabled: bool = False,
        tenant_id: UUID = None,
    ) -> Tuple[SubjectRecord, IdentityRecord]:
        return self.mem_provider.add_user(
            identifier=identifier,
            secret=secret,
            tenant_id=tenant_id or self.tenant_id,
            status=status,
            mfa_enabled=mfa_enabled,
        )


if __name__ == "__main__":
    unittest.main()
