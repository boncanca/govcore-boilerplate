"""In-Memory Reference Implementation of TenantStore and TenantResolver.

Used to test and prove the Conformance Test Suite itself.
Zero external dependencies.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence
from uuid import UUID, uuid4

from contracts.tenancy import (
    TenantIsolationModel,
    TenantRecord,
    TenantResolver,
    TenantStatus,
    TenantStore,
)


class InMemoryTenantStore:
    """Pure in-memory tenant store."""

    def __init__(self) -> None:
        self.tenants_by_id: Dict[UUID, TenantRecord] = {}
        self.tenants_by_slug: Dict[str, TenantRecord] = {}

    def add_tenant(
        self,
        slug: str,
        name: str,
        status: TenantStatus = TenantStatus.ACTIVE,
        isolation_model: TenantIsolationModel = TenantIsolationModel.DISCRIMINATOR,
    ) -> TenantRecord:
        tenant_id = uuid4()
        tenant = TenantRecord(
            tenant_id=tenant_id,
            slug=slug,
            name=name,
            status=status,
            isolation_model=isolation_model,
        )
        self.tenants_by_id[tenant_id] = tenant
        self.tenants_by_slug[slug] = tenant
        return tenant

    def get_by_id(self, tenant_id: UUID) -> Optional[TenantRecord]:
        return self.tenants_by_id.get(tenant_id)

    def get_by_slug(self, slug: str) -> Optional[TenantRecord]:
        return self.tenants_by_slug.get(slug)

    def list_active(self) -> Sequence[TenantRecord]:
        return [t for t in self.tenants_by_id.values() if t.status == TenantStatus.ACTIVE]


class InMemoryTenantResolver:
    """Pure in-memory resolver enforcing Chapter 3 Section 4 precedence."""

    def __init__(self, store: InMemoryTenantStore) -> None:
        self.store = store

    def resolve_tenant(
        self,
        host: Optional[str] = None,
        header_value: Optional[str] = None,
        subject_tenant_id: Optional[UUID] = None,
    ) -> Optional[TenantRecord]:
        # 1. Host / Subdomain
        if host:
            subdomain = host.split(".")[0].lower()
            tenant = self.store.get_by_slug(subdomain)
            if tenant:
                return tenant

        # 2. X-Tenant-ID Header
        if header_value:
            # Try by UUID or by slug
            try:
                tid = UUID(header_value)
                tenant = self.store.get_by_id(tid)
                if tenant:
                    return tenant
            except ValueError:
                tenant = self.store.get_by_slug(header_value)
                if tenant:
                    return tenant

        # 3. Subject Claim
        if subject_tenant_id:
            return self.store.get_by_id(subject_tenant_id)

        return None
