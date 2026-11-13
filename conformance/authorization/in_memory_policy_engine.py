"""In-Memory Reference Implementation of PolicyEngine.

Used to test and prove the Conformance Test Suite itself.
Zero external dependencies.
"""

from __future__ import annotations

from typing import Optional, Set, Tuple

from contracts.authorization import (
    AccessDecision,
    AccessDeniedError,
    ActionType,
    Actor,
    Decision,
    EvaluationContext,
    PolicyEngine,
    ResourceTarget,
    SecurityClassification,
)


class InMemoryPolicyEngine:
    """Pure in-memory policy engine enforcing Chapter 4 normative rules."""

    def __init__(self) -> None:
        # Set of (role, resource_type, action)
        self.role_permissions: Set[Tuple[str, str, str]] = set()

    def register_role_permission(self, role: str, resource_type: str, action: str) -> None:
        self.role_permissions.add((role, resource_type, action))

    def evaluate(
        self,
        actor: Actor,
        action: str,
        resource: ResourceTarget,
        context: Optional[EvaluationContext] = None,
    ) -> AccessDecision:
        # 1. Tenant Boundary Invariant (Chapter 4 Section 3.2)
        if actor.tenant_id != resource.tenant_id:
            return AccessDecision.deny(
                reason=f"Actor tenant {actor.tenant_id} does not match resource tenant {resource.tenant_id}",
                code="CROSS_TENANT_VIOLATION",
                policy_id="sys:isolation:tenant-boundary",
            )

        # 2. Security Classification Invariant (Chapter 4 Section 3.3)
        if resource.classification.level > actor.clearance.level:
            return AccessDecision.deny(
                reason=f"Resource classification {resource.classification.value} exceeds actor clearance {actor.clearance.value}",
                code="INSUFFICIENT_CLEARANCE",
                policy_id="sys:security:clearance-check",
            )

        # 3. Role-Based Access Check
        has_permission = any(
            (role, resource.resource_type, action) in self.role_permissions
            for role in actor.roles
        )
        if not has_permission:
            return AccessDecision.deny(
                reason=f"No matching grant for roles {list(actor.roles)} on {resource.resource_type}:{action}",
                code="NO_MATCHING_POLICY",
                policy_id="sys:rbac:default-deny",
            )

        # 4. MFA Step-Up Invariant (Chapter 4 Section 3.4)
        mfa_required_actions = {ActionType.EXPORT.value, ActionType.SIGN.value}
        if (action in mfa_required_actions or resource.classification == SecurityClassification.RESTRICTED) and not actor.mfa_verified:
            return AccessDecision.deny(
                reason="High-assurance action or restricted resource requires verified MFA session.",
                code="MFA_STEP_UP_REQUIRED",
                policy_id="sys:security:mfa-step-up",
            )

        return AccessDecision.allow(
            policy_id=f"policy:rbac:{resource.resource_type}:{action}",
            reason="Access permitted by RBAC grant",
        )

    def enforce(
        self,
        actor: Actor,
        action: str,
        resource: ResourceTarget,
        context: Optional[EvaluationContext] = None,
    ) -> None:
        decision = self.evaluate(actor, action, resource, context)
        if not decision.is_allowed:
            raise AccessDeniedError(
                message=decision.reason or "Access denied by policy engine.",
                code=decision.code,
                policy_id=decision.matched_policy_id,
            )
