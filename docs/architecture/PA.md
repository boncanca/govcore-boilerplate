# GovCore — Product Architecture (PA)

- **Document**: `docs/architecture/PA.md`
- **Type**: Product Architecture
- **Status**: Approved / Living Document
- **Authority**: [PDD](../pdd/PDD.md), [ADR-001](../adr/0001-govcore-framework-neutral-standard.md)
- **Version**: 1.0.0

---

## 1. Executive Summary & Architectural Intent

The **Product Architecture (PA)** establishes the conceptual structure, domain boundaries, and systemic relationships of GovCore.

GovCore conceptually decouples **Public-Sector Guarantees** from **Framework Plumbing**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        GOVCORE ARCHITECTURE                            │
├────────────────────────────────────────────────────────────────────────┤
│                       GOVERNANCE & SPECIFICATION                       │
│      Normative standards, security invariants, RFC requirements        │
├────────────────────────────────────────────────────────────────────────┤
│                         PROGRAMMATIC CONTRACTS                         │
│       Framework-neutral boundaries, interfaces, ports & types          │
├────────────────────────────────────────────────────────────────────────┤
│                         CONFORMANCE TESTING                            │
│           Automated behavioral verification of implementations         │
├────────────────────────────────────────────────────────────────────────┤
│                         FRAMEWORK ADAPTERS                             │
│        Django (Reference) │ FastAPI │ Flask │ Frappe / ERPNext        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Conceptual Domain Model

The GovCore domain model is organized around six interconnected subdomains:

```text
                        ┌───────────────────┐
                        │ TENANCY SUBDOMAIN │
                        │  (Org Boundaries) │
                        └─────────┬─────────┘
                                  │ scopes
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│   IDENTITY    │         │ AUTHORIZATION │         │     AUDIT     │
│   SUBDOMAIN   │         │   SUBDOMAIN   │         │   SUBDOMAIN   │
│ (Subject,     │ acts as │ (Policy,      │ records │ (Immutable,   │
│  Credentials) │────────>│  RBAC/ABAC)   │────────>│  Provenance)  │
└───────────────┘         └───────┬───────┘         └───────────────┘
                                  │ governs access to
                                  ▼
                        ┌───────────────────┐
                        │     RESOURCES     │
                        │ (Domain Entities) │
                        └───────────────────┘
```

### 2.1 The Tenancy Subdomain
- **Responsibility**: Establishes sovereign data boundaries and contextual scoping.
- **Key Concepts**: `Tenant`, `TenantContext`, `TenantIsolationStrategy` (Discriminator, Schema, Database).
- **Invariants**: Cross-tenant data leaks are impossible at the data layer; all operations carry a verified tenant context.

### 2.2 The Identity Subdomain
- **Responsibility**: Subject authentication, credential verification, and session lifecycle.
- **Key Concepts**: `Subject`, `Identity`, `Credential`, `MFAVerifier`, `SessionManager`, `ExternalIdPBinding`.
- **Invariants**: Passwords use memory-hard hashing (Argon2id); MFA is mandatory for administrative tiers; sessions support absolute and idle expirations with instant revocation.

### 2.3 The Authorization Subdomain
- **Responsibility**: Policy evaluation for requested actions on managed resources.
- **Key Concepts**: `Actor`, `Action`, `Resource`, `Policy`, `PolicyEngine`.
- **Invariants**: Default fail-closed (`DENY`); evaluation factors subject, resource classification, and runtime execution context.

### 2.4 The Audit & Provenance Subdomain
- **Responsibility**: Immutable, non-repudiable recording of security and domain occurrences.
- **Key Concepts**: `AuditEvent`, `AuditSink`, `TamperEvidenceChain`.
- **Invariants**: Logs are strictly append-only; update/delete operations are structurally prohibited; timestamps are synchronized UTC.

### 2.5 The Data Governance Subdomain
- **Responsibility**: Data classification, retention, encryption, and statutory archiving.
- **Key Concepts**: `DataClassification` (Public, Official, Confidential, Restricted), `RetentionPolicy`, `RedactionEngine`.

### 2.6 The Platform Services Subdomain
- **Responsibility**: Common infrastructure abstractions required by public services.
- **Key Concepts**: `AsyncJobContext`, `DocumentStorage`, `SecretResolver`, `CachePartition`.

---

## 3. Product Boundary & Relationship to Downstream Systems

GovCore operates as the constitutional core for any digital public service. Downstream applications (e.g., Land Registry, Citizen Welfare Portal, Business Licensing) plug directly into GovCore:

```text
┌─────────────────────────────────────────────────────────┐
│               AGENCY BUSINESS APPLICATION               │
│          (Land Registry, Citizen Portal, etc.)          │
└────────────────────────────┬────────────────────────────┘
                             │ depends on
                             ▼
┌─────────────────────────────────────────────────────────┐
│               GOVCORE FRAMEWORK ADAPTER                 │
│        (e.g., govcore-django / govcore-fastapi)         │
└────────────────────────────┬────────────────────────────┘
                             │ conforms to
                             ▼
┌─────────────────────────────────────────────────────────┐
│              GOVCORE PROGRAMMATIC CONTRACTS             │
│            (Pure Python Interfaces / Protocols)         │
└────────────────────────────┬────────────────────────────┘
                             │ expresses programmatic boundaries for
                             ▼
┌─────────────────────────────────────────────────────────┐
│                  GOVCORE SPECIFICATION                  │
│       (Normative Requirements, RFCs, Invariants)        │
└─────────────────────────────────────────────────────────┘
```
