# GovCore Specification v1.0 — Architecture & Conformance Outline

- **Version**: 1.0.0-draft
- **Status**: Proposal / Working Draft
- **Authority**: ADR-001 (Framework-Neutral Standard, Specification, and Contracts)

---

## 1. Executive Summary & Purpose

The **GovCore Specification v1.0** establishes the normative technical requirements for digital public services, sovereign government platforms, and public-sector software systems. 

It does not prescribe programming languages, database engines, or web frameworks. Instead, it mandates **security guarantees, domain lifecycles, isolation boundaries, and audit invariants** that any conforming implementation MUST satisfy.

---

## 2. Core Domain Vocabulary & Conceptual Model

Conforming implementations and programmatic contracts MUST adhere to the following domain terminology:

```text
┌─────────────────────────────────────────────────────────────┐
│                           TENANT                            │
│  (Sovereignty Boundary: Agency / Ministry / Municipality)   │
│                                                             │
│   ┌──────────────┐         acts as          ┌────────────┐  │
│   │   SUBJECT    │ ───────────────────────> │   ACTOR    │  │
│   │ (Human / Svc)│                          │ (Audited)  │  │
│   └──────────────┘                          └─────┬──────┘  │
│          │                                        │         │
│     authenticates                              executes     │
│          │                                     operation    │
│          ▼                                        │         │
│   ┌──────────────┐      evaluates policy          ▼         │
│   │  CREDENTIAL  │ ───────────────────────> ┌────────────┐  │
│   │  (Password,  │                          │  RESOURCE  │  │
│   │   TOTP, Web) │                          └─────┬──────┘  │
│   └──────────────┘                                │         │
│                                              emits event    │
│                                                   │         │
│                                                   ▼         │
│                                             ┌────────────┐  │
│                                             │AUDIT EVENT │  │
│                                             │(Immutable) │  │
│                                             └────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Vocabulary Definitions

1. **Tenant**: A sovereign organizational boundary (e.g., department, ministry, agency, municipality). A tenant represents a hard isolation boundary for data, authorization policies, and configuration.
2. **Subject**: An entity requesting access or performing an action. A subject MAY be a human civil servant, citizen, system daemon, external API consumer, or automated service account.
3. **Identity**: The verified record of a Subject within the system or linked from a sovereign Identity Provider (IdP).
4. **Credential**: An authenticator bound to an Identity (e.g., argon2-hashed password, TOTP seed, FIDO2/WebAuthn public key, mutual-TLS certificate).
5. **Actor**: The contextual manifestation of a Subject during an executed operation within a specific Tenant. The Actor carries runtime claims, IP address, user-agent, session identifiers, and security clearance.
6. **Resource**: An addressable system entity subject to governance (e.g., citizen record, permit application, document, audit entry, organization unit).
7. **Policy**: A deterministic rule or set of rules that grants or denies an Actor permission to execute an Action upon a Resource within a given Context.
8. **Action**: An operation attempted on a Resource (`create`, `read`, `update`, `delete`, `approve`, `sign`, `export`).
9. **Audit Event**: An immutable, structured, non-repudiable record capturing *Who (Actor)* did *What (Action)* to *Which entity (Resource)*, *When (Timestamp UTC)*, *Where (Tenant & Network Origin)*, *Why/Under what authorization (Policy)*, and *Outcome (Success / Denied / Error)*.
10. **Adapter**: A software package that binds a specific runtime framework (e.g., Django, FastAPI, Flask, Frappe) to the GovCore Contracts.

---

## 3. Specification Structure (Chapters Overview)

### Chapter 1: Core Domain Vocabulary & Ontologies
- Authoritative definition of entities, relationships, and state models.
- Standard identifier formatting (UUIDv4/UUIDv7, URN schemas: `urn:govcore:tenant:{id}`, `urn:govcore:subject:{id}`).

### Chapter 2: Identity, Credentials & Authentication
- **Identity Lifecycle**: Creation, verification, suspension, archival, tombstoning.
- **Credential Storage**: Mandatory cryptographic algorithms (Argon2id default for passwords, PBKDF2 minimum fallback).
- **Multi-Factor Authentication (MFA)**:
  - System MUST support step-up and mandatory MFA enforcement based on tenant policy.
  - Supported factors: TOTP (RFC 6238), WebAuthn/FIDO2, Sovereign Digital IDs (eIDAS, SAML2, OIDC).
  - Single-use cryptographically hashed recovery/backup codes.
- **Session Governance**: Absolute timeout (MUST NOT exceed 12 hours for admin interfaces), idle timeout (SHOULD NOT exceed 30 minutes), concurrent session limits, immediate revocation on privilege change.

### Chapter 3: Organization & Multi-Tenancy
- **Tenancy Models**:
  - Model A: Row/Discriminator Isolation (`tenant_id` on all tenant-scoped entities).
  - Model B: Schema Isolation (PostgreSQL schema per tenant).
  - Model C: Database/Instance Isolation (Dedicated database per sovereign tenant).
- **Context Resolution**: Deterministic resolution order (Subdomain/Host header -> Header `X-Tenant-ID` -> Authenticated Subject Claim).
- **Isolation Guarantee**: Cross-tenant data leakage MUST be impossible at the database query level (e.g., via row-level security or strict middleware context injection).

### Chapter 4: Access Control & Authorization (RBAC & ABAC)
- **Role-Based Access Control (RBAC)**: Hierarchical roles (`SuperAdmin`, `TenantAdmin`, `Officer`, `Auditor`, `Citizen`).
- **Attribute-Based Access Control (ABAC)**: Contextual policy evaluation factoring:
  - Subject attributes (clearance level, department).
  - Resource attributes (classification: Public, Internal, Confidential, Restricted).
  - Environmental attributes (network location, time-of-day, MFA verification status).
- **Fail-Closed Default**: Any operation without an explicit `ALLOW` policy MUST evaluate to `DENY`.

### Chapter 5: Immutable Audit & Provenance
- **Audit Invariants**:
  - Audit records MUST be append-only. No `UPDATE` or `DELETE` operations are permissible on audit logs.
  - Clock sources MUST be synchronized via NTP and formatted in ISO 8601 UTC with microsecond precision.
- **Log Integrity**: Audit events SHOULD support cryptographic chaining (HMAC or Merkle tree hash chaining) to prove tamper-evidence.
- **Separation of Duties**: Even a Tenant Administrator MUST NOT possess the privilege to disable, suppress, or modify audit logs.

### Chapter 6: Data Governance, Sovereignty & Retention
- **Data Classification**: Standard metadata tagging on entities (`classification: public | official | secret`).
- **Data at Rest & in Transit**: Mandatory TLS 1.3 in transit; column-level or tablespace encryption for PII/Confidential data.
- **Right to Erasure vs. Statutory Retention**: Reconciliation between privacy mandates (GDPR/APPI) and statutory retention laws (e.g., 7-year fiscal archives).

### Chapter 7: Platform Services & Integration Boundaries
- **Task Queues & Async Jobs**: Tenant context propagation through background tasks (Celery, Arq, Redis queues).
- **Document & File Storage**: Virus scanning hooks, tenant-isolated buckets/prefixes, pre-signed short-lived URLs.
- **Secrets Management**: Dynamic runtime secret loading; secrets MUST NOT be written to source control or logged.

### Chapter 8: API, Protocols & Interoperability
- **OpenAPI 3.1 & Schema Documentation**: Machine-readable API contracts.
- **Standard Envelope**:
  - Standardized success payload and metadata (`page`, `total`, `requestId`).
  - Standardized RFC 7807 (Problem Details for HTTP APIs) error response format.
- **Idempotency**: All mutating operations (`POST`, `PUT`, `PATCH`) SHOULD support `Idempotency-Key` headers.
- **Rate Limiting**: Granular rate limiting by IP, Subject, and Tenant to prevent DoS.

### Chapter 9: Conformance & Verification
- **Conformance Levels**:
  - **Level 1 (Core)**: Discriminator tenancy, RBAC, basic audit logging, standard auth.
  - **Level 2 (Enhanced)**: Mandatory MFA, schema/database isolation, ABAC policy engine, RFC 7807 error envelopes.
  - **Level 3 (High-Assurance)**: Cryptographic audit chaining, WebAuthn/FIDO2, HSM/KMS secret integration, strict zero-trust session termination.
- **Automated Verification**: How the test harness certifies an adapter.

---

## 4. Next Steps & Artifact Map

```text
Step 1: ADR-001 (Accepted)
   │
Step 2: spec/v1.0/outline.md (This Document)
   │
Step 3: spec/v1.0/01-vocabulary.md & spec/v1.0/02-identity.md (Normative Chapters)
   │
Step 4: contracts/ (Pure-Python Protocols: IdentityProvider, TenantContext, AuditSink)
   │
Step 5: conformance/ (Harness for testing any implementation)
   │
Step 6: adapters/django/ (Refactor existing codebase to fulfill contracts)
```
