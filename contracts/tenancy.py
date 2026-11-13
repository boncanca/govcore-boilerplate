"""GovCore Multi-Tenancy & Sovereign Boundary Contracts.

Normative Specification Authority:
    - Chapter 1: Core Domain Vocabulary (spec/v1.0/01-vocabulary.md)
    - Chapter 3: Organization & Multi-Tenancy (spec/v1.0/03-tenancy.md)

Architectural Boundary:
    Pure Python interfaces, protocols, and standard context structures.
    Zero framework, ORM, or database dependencies.
"""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Iterator, Mapping, Optional, Protocol, Sequence, runtime_checkable
from uuid import UUID


class TenantStatus(str, Enum):
    """Lifecycle state of a sovereign Tenant per spec Chapter 3 Section 2."""
    PROVISIONING = "PROVISIONING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    OFFBOARDED = "OFFBOARDED"


class TenantIsolationModel(str, Enum):
    """Database and runtime isolation strategy per spec Chapter 3 Section 3."""
    DISCRIMINATOR = "DISCRIMINATOR"
    SCHEMA = "SCHEMA"
    DATABASE = "DATABASE"


class TenantError(Exception):
    """Base exception for tenancy violations."""
    pass


class TenantNotFoundError(TenantError):
    """Raised when an identified tenant cannot be located in the tenant store."""
    pass


class TenantInactiveError(TenantError):
    """Raised when an operation attempts to target a PROVISIONING, SUSPENDED, or OFFBOARDED tenant."""
    pass


class TenantContextMissingError(TenantError):
    """Raised when an execution context requires an active tenant but none is bound."""
    pass


class CrossTenantAccessError(TenantError):
    """Raised when an operation attempts unauthorized access across tenant boundaries."""
    pass


@dataclass(frozen=True)
class TenantRecord:
    """Canonical representation of an isolated sovereign tenant."""
    tenant_id: UUID
    slug: str
    name: str
    status: TenantStatus = TenantStatus.ACTIVE
    isolation_model: TenantIsolationModel = TenantIsolationModel.DISCRIMINATOR
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    @property
    def canonical_urn(self) -> str:
        """Return canonical URN for this Tenant per spec Chapter 1."""
        return f"urn:govcore:tenant:{self.tenant_id}"

    @property
    def is_operational(self) -> bool:
        """Return True only if the tenant is active and accepting requests."""
        return self.status == TenantStatus.ACTIVE


@dataclass(frozen=True)
class TenantContext:
    """Execution context bound to the active thread, coroutine, or task."""
    tenant: Optional[TenantRecord] = None
    is_global: bool = False
    correlation_id: Optional[str] = None

    @property
    def has_active_tenant(self) -> bool:
        """Check if context carries an operational tenant."""
        return self.tenant is not None and self.tenant.is_operational


@runtime_checkable
class TenantStore(Protocol):
    """Port for querying and retrieving sovereign tenants from persistence."""

    def get_by_id(self, tenant_id: UUID) -> Optional[TenantRecord]:
        """Retrieve a tenant by unique UUID."""
        ...

    def get_by_slug(self, slug: str) -> Optional[TenantRecord]:
        """Retrieve a tenant by human-readable unique slug."""
        ...

    def list_active(self) -> Sequence[TenantRecord]:
        """List all operational active tenants."""
        ...


@runtime_checkable
class TenantResolver(Protocol):
    """Port for resolving the active tenant from incoming request metadata.
    
    Enforces the deterministic resolution order mandated by Chapter 3 Section 4.
    """

    def resolve_tenant(
        self,
        host: Optional[str] = None,
        header_value: Optional[str] = None,
        subject_tenant_id: Optional[UUID] = None,
    ) -> Optional[TenantRecord]:
        """Resolve a TenantRecord from host, header, or subject claims in priority order."""
        ...


@runtime_checkable
class TenantContextManager(Protocol):
    """Port for managing and propagating tenant execution context across execution flows."""

    def get_current_context(self) -> TenantContext:
        """Return the currently bound execution context."""
        ...

    def require_current_tenant(self) -> TenantRecord:
        """Return the active TenantRecord, or raise TenantContextMissingError / TenantInactiveError."""
        ...

    def set_current_context(self, context: TenantContext) -> None:
        """Explicitly bind the active tenant context."""
        ...

    def clear_context(self) -> None:
        """Clear any bound tenant context from the current execution environment."""
        ...


class DefaultTenantContextManager:
    """Thread-safe and coroutine-safe context manager powered by standard contextvars."""

    _var: contextvars.ContextVar[TenantContext] = contextvars.ContextVar(
        "govcore_tenant_context",
        default=TenantContext(tenant=None, is_global=False),
    )

    def get_current_context(self) -> TenantContext:
        return self._var.get()

    def require_current_tenant(self) -> TenantRecord:
        ctx = self.get_current_context()
        if ctx.is_global:
            raise TenantContextMissingError("Current execution is flagged global; no specific tenant bound.")
        if ctx.tenant is None:
            raise TenantContextMissingError("No tenant context bound to current execution.")
        if not ctx.tenant.is_operational:
            raise TenantInactiveError(f"Tenant {ctx.tenant.slug} is {ctx.tenant.status.value}, not ACTIVE.")
        return ctx.tenant

    def set_current_context(self, context: TenantContext) -> None:
        self._var.set(context)

    def clear_context(self) -> None:
        self._var.set(TenantContext(tenant=None, is_global=False))

    @contextmanager
    def scope_context(self, context: TenantContext) -> Iterator[TenantContext]:
        """Scoped execution block restoring prior context upon exit."""
        token = self._var.set(context)
        try:
            yield context
        finally:
            self._var.reset(token)
