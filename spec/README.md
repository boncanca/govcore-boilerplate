# GovCore Specification System

The **GovCore Specification** defines the authoritative, framework-neutral standard for building secure, auditable, interoperable, and multi-tenant government and public-sector software.

---

## 1. Governance and Purpose

The GovCore Specification operates as the **constitutional layer** of the GovCore ecosystem. It defines **what guarantees, lifecycles, and security boundaries must exist**, leaving runtime mechanics to framework adapters.

```text
                 GOVCORE STANDARD
                       │
          ┌────────────┴────────────┐
          │                         │
       SPECIFICATION             CONTRACTS
     normative rules          programmatic ports
     (spec/)                  (contracts/)
          │                         │
          └────────────┬────────────┘
                       │
                CONFORMANCE TESTS
                (conformance/)
                       │
       ┌───────────────┼───────────────┐
       │               │               │
     Django          FastAPI         Frappe
   Reference        Adapter         Adapter
 Implementation
```

### Decoupled Versioning
- **Specification (`spec/`)** is versioned independently (e.g., `v1.0`, `v1.1`, `v2.0`). It specifies requirements without depending on any programming language.
- **Contracts (`contracts/`)** define the programmatic interfaces (e.g., Python `typing.Protocol`, TypeScript types) implementing a specific Specification version.
- **Adapters (`adapters/`)** implement the contracts for a specific framework and release on their own lifecycle.

---

## 2. Normative Language & Requirement Levels

The key words **"MUST"**, **"MUST NOT"**, **"REQUIRED"**, **"SHALL"**, **"SHALL NOT"**, **"SHOULD"**, **"SHOULD NOT"**, **"RECOMMENDED"**, **"NOT RECOMMENDED"**, **"MAY"**, and **"OPTIONAL"** in this specification are to be interpreted as described in BCP 14 [[RFC 2119](https://www.ietf.org/rfc/rfc2119.txt)] [[RFC 8174](https://www.ietf.org/rfc/rfc8174.txt)] when, and only when, they appear in all capitals, as shown here.

| Requirement Level | Conformance Definition |
|---|---|
| **MUST / REQUIRED / SHALL** | Absolute requirement of the specification. An implementation that fails to satisfy this cannot claim GovCore conformance. |
| **MUST NOT / SHALL NOT** | Absolute prohibition of the specification. |
| **SHOULD / RECOMMENDED** | Valid reasons may exist in particular circumstances to ignore a particular item, but the full implications must be understood and carefully weighed before choosing a different course. |
| **SHOULD NOT / NOT RECOMMENDED** | Valid reasons may exist when the particular behavior is acceptable or even useful, but the full implications should be understood and the case carefully weighed. |
| **MAY / OPTIONAL** | Truly optional; one vendor or agency may choose to include the item because a particular marketplace requires it or because the vendor feels that it enhances the product while another vendor may omit the same item. |

---

## 3. Specification Structure (v1.0)

Specifications are organized into numbered chapters under versioned directories (e.g., `spec/v1.0/`):

- **[spec/v1.0/outline.md](v1.0/outline.md)**: Specification Outline, Master Index, and Conformance Matrix.
- **Chapter 1: Domain Vocabulary & Core Ontologies**: Authoritative definitions of Subject, Actor, Tenant, Policy, Audit Event, etc.
- **Chapter 2: Identity & Authentication**: Credential management, session lifecycles, MFA challenge/verify flows, IdP federations.
- **Chapter 3: Organization & Multi-Tenancy**: Tenant resolution, data isolation boundaries, lifecycle transitions.
- **Chapter 4: Authorization & Policy Enforcement**: RBAC, ABAC, contextual policy evaluation, permission delegation.
- **Chapter 5: Immutable Audit & Provenance**: Audit taxonomy, tamper-evident log chains, actor attribution, event persistence.
- **Chapter 6: Data Governance, Sovereignty & Retention**: Data classification levels, encryption requirements, retention and purge lifecycles.
- **Chapter 7: Platform Services & Integration Boundaries**: File storage security, async queues, secret isolation, cache partitions.
- **Chapter 8: API, Protocols & Interoperability**: OpenAPI standards, standardized error envelopes, idempotency keys, rate limiting.
- **Chapter 9: Conformance & Verification**: Conformance levels (Core, Enhanced, High-Assurance), verification methodology.
