# GovCore — Technical Architecture (TA)

- **Document**: `docs/architecture/TA.md`
- **Type**: Technical Architecture
- **Status**: Approved / Living Document
- **Authority**: [PDD](../pdd/PDD.md), [PA](PA.md), [ADR-001](../adr/0001-govcore-framework-neutral-standard.md)
- **Version**: 1.0.0

---

## 1. Technical Strategy & Repository Layout

The Technical Architecture organizes GovCore into four concrete engineering layers:

```text
govcore/
│
├── docs/                               # Governance & Architecture Documentation
│   ├── pdd/                            # Product Design Document (Product Intent & Scope)
│   ├── architecture/                   # PA (Conceptual) & TA (Concrete Technical)
│   │   ├── PA.md
│   │   └── TA.md
│   └── adr/                            # Architecture Decision Records (Cross-cutting)
│       └── 0001-govcore-framework-neutral-standard.md
│
├── spec/                               # Normative Standard ("The Constitution")
│   └── v1.0/
│       ├── README.md                   # Spec System & RFC 2119 Rules
│       ├── outline.md                  # Master Index & Conformance Matrix
│       ├── 01-vocabulary.md            # Domain Ontologies & Identifiers
│       ├── 02-identity-and-auth.md     # Identity & Authentication Spec
│       └── ...
│
├── contracts/                          # Pure Programmatic Ports (PEP 544 Protocols)
│   ├── identity.py                     # IdentityProvider, CredentialVerifier, MFAService
│   ├── tenancy.py                      # TenantContextManager, TenantResolver
│   ├── authorization.py                # PolicyEngine, AccessDecision
│   └── audit.py                        # AuditSink, AuditEventRecord
│
├── conformance/                        # Automated Verification Test Suite
│   ├── harness.py                      # Abstract test runners & fixtures
│   ├── identity/                       # Identity conformance test suite
│   ├── tenancy/                        # Tenancy isolation test suite
│   ├── authorization/                  # Policy evaluation test suite
│   └── audit/                          # Audit immutability test suite
│
└── adapters/                           # Conforming Framework Implementations
    ├── django/                         # Django Reference Implementation
    ├── fastapi/                        # FastAPI High-Throughput Adapter
    ├── flask/                          # Flask Lightweight Adapter
    └── frappe/                         # Frappe / ERPNext Adapter
```

---

## 2. Programmatic Contracts Architecture (`contracts/`)

### 2.1 Pure Python Protocol Design
Contracts MUST NOT import web frameworks (Django, FastAPI, Flask, Frappe) or database ORMs. They rely on standard library typing (`typing.Protocol`, `@runtime_checkable`, `dataclasses`, `enum`).

```python
from typing import Protocol, runtime_checkable
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class TenantContext:
    tenant_id: UUID
    name: str
    is_active: bool

@runtime_checkable
class TenantContextManager(Protocol):
    def get_current_tenant(self) -> TenantContext:
        """Resolve the active tenant context for the executing thread/coroutine."""
        ...
        
    def set_current_tenant(self, tenant: TenantContext) -> None:
        """Bind the active tenant context."""
        ...
```

### 2.2 Benefits of Structural Typing (PEP 544)
Using `Protocol` allows framework adapters to fulfill contracts implicitly (duck typing with static verification) or explicitly, without introducing hard inheritance coupling across packages.

---

## 3. Conformance Architecture (`conformance/`)

The Conformance Suite is a framework-agnostic verification harness written using `pytest`.

```text
┌────────────────────────────────────────────────────────┐
│               CONFORMANCE TEST HARNESS                 │
├────────────────────────────────────────────────────────┤
│  - Parameterized test classes                          │
│  - Abstract fixture factories                          │
│  - Property-based tests (Hypothesis) for boundaries   │
└───────────────────────────┬────────────────────────────┘
                            │ tests any candidate adapter
                            ▼
┌────────────────────────────────────────────────────────┐
│             ADAPTER UNDER VERIFICATION                 │
│         (e.g., adapters/django or adapters/fastapi)    │
└────────────────────────────────────────────────────────┘
```

### 3.1 Verification Example
To certify an adapter, the adapter author creates a small test file subclassing the abstract conformance suite and providing their concrete provider:

```python
from conformance.identity import BaseIdentityProviderConformanceTests
from adapters.django.identity.provider import DjangoIdentityProvider

class TestDjangoIdentityConformance(BaseIdentityProviderConformanceTests):
    def get_provider(self):
        return DjangoIdentityProvider()
```

When all tests pass, the adapter is proven compliant with the specification.

---

## 4. Security & Cryptographic Architecture

1. **Password Hashing**: Enforced via Argon2id (`argon2_cffi`). Legacy upgrade hooks run automatically upon successful legacy verification.
2. **MFA Engine**: TOTP RFC 6238 generation and verification using CSPRNG seeds stored via authenticated AES-256-GCM. Replay protection enforces single-use per 30-second window.
3. **Session Revocation**: Centralized session cache (Redis / DB) keyed by `(subject_id, session_id)` with global token generation counters allowing instant revocation of all subject sessions simultaneously.
4. **Audit Immutability**: Write-only database credentials or database trigger constraints preventing `UPDATE` and `DELETE` on audit tables. Optional cryptographic SHA-256 hash chaining.

---

## 5. Tenancy Isolation Architecture

Adapters MUST support one or more of the three standard isolation strategies:
- **Strategy A (Discriminator)**: Automatic query filtering via ORM managers (`tenant_id = context.tenant_id`) and database row-level security (RLS).
- **Strategy B (Schema)**: PostgreSQL search path routing (`SET search_path TO tenant_<id>`).
- **Strategy C (Database)**: Dynamic database connection routing based on active `TenantContext`.

---

## 6. API & Error Architecture

All API endpoints conforming to GovCore MUST return errors formatted according to **RFC 7807 (Problem Details for HTTP APIs)**:

```json
{
  "type": "https://govcore.org/errors/insufficient-clearance",
  "title": "Insufficient Security Clearance",
  "status": 403,
  "detail": "Subject clearance level OFFICIAL cannot access RESTRICTED resource.",
  "instance": "urn:govcore:audit:tenant-001:evt-99120",
  "code": "SECURITY_CLEARANCE_DENIED",
  "requestId": "req-20261008-88219"
}
```
