# GovCore Specification v1.0 — Chapter 3: Organization & Multi-Tenancy

- **Document**: `spec/v1.0/03-tenancy.md`
- **Version**: 1.0.0-draft
- **Status**: Proposal / Working Draft
- **Authority**: [ADR-001](../../docs/adr/0001-govcore-framework-neutral-standard.md)

---

## 1. Scope & Objective

This chapter specifies the normative architectural rules and behavioral guarantees for **Multi-Tenancy, Sovereign Boundary Isolation, Context Resolution, and Context Propagation** across GovCore-compliant systems.

---

## 2. Tenancy Lifecycle & Invariants

A Tenant represents a sovereign administrative boundary (e.g., ministry, state department, municipality, public corporation). Every Tenant MUST conform to the following lifecycle:

```text
 ┌──────────────┐
 │ PROVISIONING │
 └──────┬───────┘
        │ schema/resources allocated
        ▼
 ┌──────────────┐  admin/statutory  ┌──────────────┐
 │    ACTIVE    │ ────────────────> │  SUSPENDED   │
 │ (Operational)│ <──────────────── │ (Read-Only   │
 └──────┬───────┘     restored      │  or Locked)  │
        │                           └──────────────┘
        │ offboarding initiated
        ▼
 ┌──────────────┐
 │ OFFBOARDED   │ (Data archived/purged per statutory retention)
 └──────────────┘
```

### 2.1 Lifecycle States
1. **`PROVISIONING`**: Tenant infrastructure, databases, schemas, or seed policies are being initialized. Operational access MUST be blocked.
2. **`ACTIVE`**: Tenant is fully operational. Subjects belonging to this tenant may authenticate and execute permitted operations.
3. **`SUSPENDED`**: Tenant access is administratively or regulatorily suspended. All mutating requests MUST be rejected. Active sessions for all tenant subjects SHOULD be invalidated immediately.
4. **`OFFBOARDED`**: Tenant is decommissioned. All tenant data is locked for statutory archival or purged in accordance with data sovereignty rules.

---

## 3. Tenancy Isolation Models

Conforming adapters MUST support at least one of the following three isolation strategies, and MAY support hybrid configurations:

| Model | Isolation Mechanism | Target Public-Sector Workload |
|---|---|---|
| **Model A: Discriminator (Row)** | All entities include a non-nullable `tenant_id`. Database queries strictly filter by active `tenant_id` (via ORM or Row-Level Security). | Standard public portals, high-density citizen services. |
| **Model B: Schema Isolation** | Dedicated database schema per tenant (e.g., PostgreSQL `SET search_path`). Shared database instance. | Regulated departmental workloads requiring logical namespace separation. |
| **Model C: Database / Instance** | Physically dedicated database or microservice instance per tenant. Dynamic connection routing. | High-assurance sovereign ministries (defense, national intelligence, central banking). |

### 3.1 Non-Leakage Invariant
Under all models, **cross-tenant data access is strictly forbidden** unless governed by an explicit, authenticated, and audited cross-tenant sharing contract. An operation executing within Tenant $A$ MUST NOT be able to read, update, or infer the existence of records belonging to Tenant $B$.

---

## 4. Tenant Context Resolution

When a request arrives at a GovCore boundary, the system MUST resolve the active `TenantContext` in a deterministic order.

### 4.1 Resolution Priority
1. **Host / Subdomain**: (e.g., `health.gov.example` or `tenant-001.portal.gov`).
2. **Standard HTTP Header**: `X-Tenant-ID` (used for internal service-to-service calls).
3. **Authenticated Subject Claim**: The tenant ID bound to the verified session token or JWT (`tid` claim).

### 4.2 Resolution Failure
If a tenant cannot be unambiguously resolved for a tenant-scoped endpoint, the request MUST be rejected with HTTP 400 or HTTP 404, returning an RFC 7807 problem details response.

---

## 5. Context Propagation & Thread Safety

1. **Execution Safety**: The active `TenantContext` MUST be bound to the executing execution context (e.g., thread-local, `contextvars.ContextVar`, or coroutine context).
2. **Asynchronous & Background Jobs**: When dispatching asynchronous tasks (e.g., Celery, Arq, Redis queues, background threads), the originating `tenant_id` and correlation metadata MUST be serialized and explicitly restored within the worker task prior to job execution.
3. **Fail-Closed Context**: Any database query executed in a tenant-scoped worker or request without an active `TenantContext` MUST raise a fatal `TenantContextMissingError` and abort immediately.
