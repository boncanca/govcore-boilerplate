# GovCore Specification v1.0 — Chapter 1: Core Domain Vocabulary & Ontologies

- **Document**: `spec/v1.0/01-vocabulary.md`
- **Version**: 1.0.0-draft
- **Status**: Proposal / Working Draft
- **Authority**: [ADR-001](../../docs/adr/0001-govcore-framework-neutral-standard.md)

---

## 1. Scope & Purpose

This chapter specifies the authoritative domain ontologies, universal identifiers, and conceptual boundaries for GovCore-compliant systems. Conforming contracts, data schemas, and runtime adapters MUST use these definitions and invariant relationships.

---

## 2. Universal Identifier Conventions

All GovCore entities MUST be addressable via canonical identifiers to guarantee interoperability across federated government agencies, databases, and microservices.

### 2.1 Identifier Formats
1. Primary entity identifiers MUST use either **UUIDv4** (random) or **UUIDv7** (time-ordered, RECOMMENDED for high-ingestion audit logs and entities).
2. Distributed or federated references MUST use canonical Uniform Resource Names (URNs) adhering to the following namespace syntax:

```text
urn:govcore:<entity_type>:<scope>:<identifier>
```

#### Canonical URN Namespaces
- **Tenant**: `urn:govcore:tenant:<tenant_id>`
- **Subject**: `urn:govcore:subject:<tenant_id>:<subject_id>` (or `urn:govcore:subject:global:<subject_id>` for cross-tenant subjects)
- **Actor**: `urn:govcore:actor:<session_or_execution_id>`
- **Resource**: `urn:govcore:resource:<tenant_id>:<resource_type>:<resource_id>`
- **Policy**: `urn:govcore:policy:<tenant_id>:<policy_id>`
- **Audit Event**: `urn:govcore:audit:<tenant_id>:<event_id>`

---

## 3. Core Entities & Invariants

```text
 ┌────────────────────────────────────────────────────────┐
 │                         TENANT                         │
 │                   (Isolation Boundary)                 │
 └───────────────────────────┬────────────────────────────┘
                             │ owns / scopes
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   SUBJECT    │      │   RESOURCE   │      │    POLICY    │
│ (Identity &  │      │ (Governed    │      │ (Access Rule │
│ Credentials) │      │  Entity)     │      │  Definition) │
└──────┬───────┘      └──────▲───────┘      └──────▲───────┘
       │ acts as             │                     │
       ▼                     │ evaluates on        │ evaluates with
┌──────────────┐             │                     │
│    ACTOR     │─────────────┴─────────────────────┘
│ (Execution   │
│   Context)   │─────────────┐
└──────────────┘             ▼
                      ┌──────────────┐
                      │ AUDIT EVENT  │
                      │ (Immutable)  │
                      └──────────────┘
```

### 3.1 Tenant
- **Definition**: A sovereign organizational boundary (e.g., ministry, state department, agency, municipal government) that encapsulates data, users, configurations, and policies.
- **Invariants**:
  - Every operational request MUST execute within the context of a resolved Tenant, or within an explicit `SystemGlobal` context reserved for platform orchestration.
  - Data belonging to one Tenant MUST NOT be accessible or visible to another Tenant unless explicitly permitted by an authorized, audited cross-tenant sharing contract.

### 3.2 Subject
- **Definition**: A distinct entity recognized by the system that is capable of requesting actions or holding permissions.
- **Subtypes**:
  - `HumanSubject`: An individual civil servant, contractor, citizen, or external auditor.
  - `ServiceSubject`: An automated system account, background daemon, or integrated external microservice.
- **Invariants**:
  - A Subject MUST have exactly one primary status in the Identity Lifecycle (`PENDING_VERIFICATION`, `ACTIVE`, `LOCKED`, `SUSPENDED`, `TOMBSTONED`).
  - A Subject MAY hold memberships in multiple Tenants, but each membership MUST maintain distinct role assignments and access rights.

### 3.3 Identity & Credential
- **Definition (Identity)**: The canonical record binding a Subject to authentication metadata, demographic/profile attributes, and external Identity Provider (IdP) linkages.
- **Definition (Credential)**: A secret or cryptographic proof bound to an Identity used to verify authenticity.
- **Invariants**:
  - Credentials MUST NOT be stored in plaintext. Passwords MUST be hashed using memory-hard, modern algorithms (Argon2id mandatory default).
  - An Identity MAY possess zero or more multi-factor authenticators (MFA) and zero or more external federated identity links (OIDC, SAML, eIDAS).

### 3.4 Actor
- **Definition**: The transient, runtime representation of an authenticated Subject actively executing an operation within a specific Tenant.
- **Required Metadata**:
  - `subject_id`: Canonical identifier of the authenticated Subject.
  - `tenant_id`: Canonical identifier of the active Tenant context.
  - `session_id`: Unique identifier of the user session or API token.
  - `client_ip`: Network IP address from which the request originated.
  - `user_agent`: Client software identifier.
  - `claims`: List of verified scopes, roles, and clearance attributes active for this specific execution.
- **Invariants**:
  - Every mutating or audited operation MUST be attributed to an explicit Actor. Anonymous execution is STRICTLY PROHIBITED for non-public operations.

### 3.5 Resource
- **Definition**: Any managed entity, domain object, or digital asset governed by the platform (e.g., application submission, citizen permit, audit log, configuration record).
- **Required Attributes**:
  - `resource_id`: Unique identifier within its type.
  - `resource_type`: Qualified domain type (e.g., `citizen_record`, `grant_application`).
  - `tenant_id`: Sovereign owner of the resource (or `global`).
  - `classification`: Security classification level (`PUBLIC`, `OFFICIAL`, `CONFIDENTIAL`, `RESTRICTED`).

### 3.6 Policy & Action
- **Definition (Action)**: A discrete operation attempted by an Actor upon a Resource (e.g., `create`, `read`, `update`, `delete`, `approve`, `sign`, `export`).
- **Definition (Policy)**: A deterministic set of access control rules combining RBAC (Role-Based) and ABAC (Attribute-Based) conditions that evaluates an `(Actor, Action, Resource, Context)` tuple to either `ALLOW` or `DENY`.
- **Invariants**:
  - Access control evaluation MUST default to `DENY` ("fail-closed").

### 3.7 Audit Event
- **Definition**: A tamper-evident, append-only record capturing a significant security, lifecycle, or domain occurrence.
- **Invariants**:
  - Audit Events MUST be immutable. Conforming implementations MUST NOT provide API endpoints, database triggers, or administrative interfaces that allow updating or deleting audit records.
  - All timestamps MUST be recorded in UTC according to ISO 8601 with at least millisecond precision.

---

## 4. Conformance Criteria

A runtime implementation or adapter claiming conformance with Chapter 1 MUST:
1. Support universal entity identification via UUIDv4/v7 and canonical URN mapping.
2. Maintain strict separation between `Subject` (permanent identity) and `Actor` (runtime execution context).
3. Ensure all domain operations operate within an unambiguous `Tenant` boundary.
4. Enforce fail-closed evaluation defaults across all resources.
