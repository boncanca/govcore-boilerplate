# GovCore — Product Design Document (PDD)

- **Document**: `docs/pdd/PDD.md`
- **Type**: Product Design Document
- **Status**: Approved / Living Document
- **Version**: 1.0.0

---

## 1. Product Vision & Intent

### 1.1 What We Are Designing
**GovCore** is a framework-neutral standard, reference architecture, and programmatic contract system for building secure, auditable, interoperable, and multi-tenant software for governments and the public sector.

GovCore is not a simple starter template or proprietary framework. It is an **open standard and software architecture** ("constitution") that establishes the required guarantees, domain models, and security boundaries for public-sector workloads, paired with concrete programmatic contracts and framework adapters.

### 1.2 The Core Problem
Government agencies and digital ministries suffer from:
1. **Framework fragmentation**: Teams build identical identity, tenancy, and audit mechanics repeatedly across Django, FastAPI, Flask, and Frappe.
2. **Compliance leakage**: Regulatory requirements (immutable audit trails, sovereign tenancy isolation, mandatory MFA, zero-trust sessions) are frequently reimplemented as ad-hoc application code, making security audits expensive and inconsistent.
3. **Vendor & runtime lock-in**: Bespoke boilerplates bind domain logic directly to specific database drivers or web frameworks.

### 1.3 Solution Hypothesis
By defining a rigorous **normative specification (`spec/`)** and **language-agnostic programmatic boundary (`contracts/`)**, public-sector projects can use their preferred framework (Django, FastAPI, Frappe) while guaranteeing 100% compliance with government security and audit mandates.

---

## 2. Stakeholders & User Personas

| Persona | Role | Primary Goal with GovCore |
|---|---|---|
| **Digital Ministry Architect** | Enterprise Architect | Standardize software architecture across cross-agency teams without forcing a single programming language or web framework. |
| **Security & Compliance Auditor** | ISO 27001 / SOC 2 / FedRAMP / GovCloud Auditor | Verify that applications conform to deterministic security, isolation, and auditability guarantees using automated conformance tests. |
| **Backend Engineer** | Application Developer (Django / FastAPI / Frappe) | Build agency business logic rapidly on top of battle-tested, pre-certified government contracts without reinventing auth, tenancy, or audit. |
| **Platform / DevOps Engineer** | Infrastructure Operator | Deploy sovereign, multi-tenant services with predictable context propagation, logging, and security boundaries. |

---

## 3. Product Capabilities & Functional Scope

GovCore defines six foundational domain capabilities:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        GOVCORE CAPABILITIES                            │
├────────────────────┬────────────────────┬──────────────────────────────┤
│ 1. Sovereign       │ 2. High-Assurance  │ 3. Deterministic             │
│    Tenancy         │    Identity & Auth │    Authorization             │
│  - Boundary isol.  │  - Argon2id hashes │  - Fail-closed default       │
│  - Context propag. │  - Mandatory MFA   │  - RBAC + ABAC               │
│  - Multi-org data  │  - Zero-trust sess │  - Contextual policies       │
├────────────────────┼────────────────────┼──────────────────────────────┤
│ 4. Immutable       │ 5. Data Governance │ 6. Interoperable             │
│    Audit Trail     │    & Sovereignty   │    API Boundary              │
│  - Append-only     │  - Classification  │  - OpenAPI 3.1               │
│  - Actor attribut. │  - Crypt. at rest  │  - RFC 7807 problem details  │
│  - Tamper evidence │  - Stat. retention │  - Idempotency guarantees    │
└────────────────────┴────────────────────┴──────────────────────────────┘
```

---

## 4. Workflows & Developer Experience

### 4.1 Adopting GovCore as an Application Team
1. **Select an Adapter**: An agency chooses the runtime adapter appropriate for their workload (e.g., `govcore-django` for full-featured portals, `govcore-fastapi` for high-throughput APIs, `govcore-frappe` for enterprise back-office ERP).
2. **Implement Business Logic via Contracts**: The application implements domain models and services bounded by `govcore.contracts`.
3. **Run Conformance Verification**: The agency executes the automated GovCore Conformance Suite (`conformance/`) in CI/CD to certify compliance with the standard prior to production deployment.

### 4.2 Verifying Compliance in Procurement
Procurement bodies specify **"GovCore Level 2 Conformance"** as an acceptance criterion in public tenders. Vendors submit automated conformance test results proving compliance, eliminating manual audit friction.

---

## 5. Scope Boundaries

### In Scope
- Normative specifications for identity, tenancy, access control, audit, data governance, and APIs.
- Pure programmatic contracts (interfaces/protocols) decoupled from web runtimes.
- Automated conformance test suites.
- Reference implementations and production adapters (Django, FastAPI, Flask, Frappe).

### Out of Scope (Non-Goals)
- Opinionated frontend presentation frameworks (GovCore is frontend-agnostic).
- Specific proprietary database vendor locking (implementations may use PostgreSQL, MySQL, CockroachDB, etc.).
- Department-specific domain workflows (e.g., specific tax laws, citizen permit schemas—these are built *on top* of GovCore).
