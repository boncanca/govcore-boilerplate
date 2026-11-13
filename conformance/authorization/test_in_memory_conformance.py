"""Verification of Authorization Conformance Suite using InMemoryPolicyEngine."""

import unittest

from conformance.authorization.in_memory_policy_engine import InMemoryPolicyEngine
from conformance.authorization.suite import BaseAuthorizationConformanceTestSuite
from contracts.authorization import PolicyEngine


class TestInMemoryAuthorizationConformance(BaseAuthorizationConformanceTestSuite, unittest.TestCase):
    """Executes the complete BaseAuthorizationConformanceTestSuite against reference implementation."""

    def create_policy_engine(self) -> PolicyEngine:
        self.mem_engine = InMemoryPolicyEngine()
        return self.mem_engine

    def register_role_permission(self, role: str, resource_type: str, action: str) -> None:
        self.mem_engine.register_role_permission(role=role, resource_type=resource_type, action=action)


if __name__ == "__main__":
    unittest.main()
