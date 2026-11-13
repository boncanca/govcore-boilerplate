# ADR-001: Adoption of Framework-Neutral Standard, Specification, and Contracts

- **Status**: Accepted
- **Date**: 2026-10-08
- **Deciders**: Architecture Working Group
- **Consulted**: Core Maintainers, Security & Governance Stakeholders

---

## 1. Context and Problem Statement

The repository was initially organized as `govcore-boilerplate`, conceived as a turnkey Django starter template for public-sector software. During technical and architectural audits, this positioning led to fundamental contradictions:

1. **Scaffold vs. Missing Code Ambiguity**: Extension points, provider abstractions, and pluggable authentication/tenancy boundaries were frequently evaluated as "incomplete Django features" rather than intentional architectural ports.
2. **Heterogeneous Public-Sector Runtimes**: Government agencies, digital ministries, and public bodies do not standardize on a single runtime or web framework. Production deployments span Django, FastAPI microservices, Flask data gateways, and Frappe/ERPNext business applications.
3. **Coupling Compliance to Runtime Plumbing**: High-assurance public-sector requirements—immutable audit logging, multi-tenant boundary isolation, multi-factor authentication (MFA) lifecycles, and zero-trust session policies—were bound to Django ORM models and middleware instead of living as verifiable, framework-neutral specifications.

A strategic pivot is required: GovCore cannot simply be a Django starter kit. It must serve as the authoritative standard and architectural constitution for government-grade systems.

---

## 2. Decision

We establish GovCore as:

> **A framework-neutral standard, reference architecture, and set of contracts for building secure, auditable, interoperable, and multi-tenant government and public-sector software.**

To achieve this without conflating documentation, language bindings, and framework code, GovCore adopts a layered architectural model:

```text
                        GOVCORE STANDARD
                               │
            ┌──────────────────┴──────────────────┐
            │                                     │
      SPECIFICATION                           CONTRACTS
   (Normative Rules, RFCs,                (Programmatic Ports,
    Domain Invariants)                     Protocols, Types)
            │                                     │
            └──────────────────┬──────────────────┘
                               │
                       CONFORMANCE TESTS
                        (conformance/)
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
         Django             FastAPI             Frappe
        Reference           Adapter            Adapter
     Implementation
```

### 2.1 The Architectural Layers

1. **Specification (`spec/`)**:
   - The authoritative "Constitution" of GovCore.
   - Completely language- and framework-agnostic.
   - Written using normative requirement levels ([RFC 2119](https://www.ietf.org/rfc/rfc2119.txt) / [RFC 8174](https://www.ietf.org/rfc/rfc8174.txt): `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`).
   - Defines domain vocabulary, lifecycle state machines, security invariants, error models, and audit taxonomy.

2. **Contracts (`contracts/`)**:
   - The programmatic port definitions (initially pure Python via PEP 544 `typing.Protocol` / Abstract Base Classes, zero framework dependencies).
   - Translates specification guarantees into software interfaces (`IdentityProvider`, `TenantContextManager`, `AuditLogger`, `AuthorizationPolicyEngine`).
   - Independently versionable to ensure Python (or any other language runtime in the future) is not a hidden prerequisite for the specification itself.

3. **Conformance Test Suite (`conformance/`)**:
   - A reusable test harness that validates whether a candidate implementation complies with GovCore contracts and behavioral guarantees.
   - Operates against any adapter satisfying the contracts to determine compliance.

4. **Adapters & Reference Implementations (`adapters/`)**:
   - Framework-specific adapters that fulfill the contracts using framework-native idioms.
   - **Django** is designated as the primary, production-grade **Reference Implementation**.
   - Subsequent adapters will target FastAPI, Flask, and Frappe.

### 2.2 Documentation & Design Hierarchy

GovCore aligns its documentation and design artifacts according to the following lineage:

```text
PDD — Product Design Document (docs/pdd/PDD.md)
   │  What are we designing? Stakeholders, capabilities, scope, workflows.
   ▼
PA  — Product Architecture (docs/architecture/PA.md)
   │  What is the conceptual architecture? Subdomains & conceptual boundaries.
   ▼
TA  — Technical Architecture (docs/architecture/TA.md)
   │  How is it technically realized? Contracts, security, data & adapters.
   │
ADR — Architecture Decision Records (docs/adr/)
      Cuts across PA, TA, and SPEC to record significant decisions.
```

The normative **Specification (`spec/`)** is maintained as a first-class top-level directory rather than an internal TA sub-item because GovCore itself *is* a standard, maintaining an unambiguous distinction between *how GovCore is designed* and *what GovCore-compliant implementations MUST do*.

---

## 3. Consequences

### Positive Consequences
- **Clear Separation of Concerns**: "What must exist" (the Specification) is separated from "How it is invoked in code" (the Contracts) and "How it is executed in a framework" (the Adapter).
- **Audit Clarity**: External security and compliance auditors evaluate conformance against the unambiguous, normative Specification rather than framework-specific glue code.
- **Portability & Interoperability**: Government platforms can combine Django portals, FastAPI microservices, and Frappe ERP modules under a unified GovCore security and tenancy model.
- **Strict Clean / Hexagonal Architecture**: Core domain contracts cannot accidentally leak framework dependencies (Django ORM querysets, request contexts, or framework settings).

### Negative / Trade-Offs
- **Documentation Overhead**: Requires drafting and maintaining rigorous specification documents prior to implementing new features.
- **Initial Restructuring Effort**: The repository structure and namespace must be reorganized to separate specification, contracts, and the Django reference implementation.
- **Indirection**: Implementing a feature in Django requires establishing the specification clause and contract interface first, rather than writing ad-hoc Django models/views.

---

## 4. Implementation Phasing

1. **Phase 1: Foundation (Current)**
   - Adopt ADR-001.
   - Establish GovCore Specification v1.0 Outline, Normative Language Rules, and Core Domain Vocabulary.
2. **Phase 2: Programmatic Contracts**
   - Create pure-Python `contracts/` with zero Django or external framework imports.
3. **Phase 3: Conformance Suite & Django Alignment**
   - Implement the automated conformance test suite.
   - Refactor existing Django modules (`core.identity`, tenancy, audit) to conform cleanly to `contracts/`.
4. **Phase 4: Adapter Expansion**
   - Deliver subsequent adapters for FastAPI, Flask, and Frappe based on community and agency demand.
