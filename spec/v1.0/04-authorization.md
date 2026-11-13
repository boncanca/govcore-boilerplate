# GovCore Specification v1.0 — Chapter 4: Access Control & Authorization

- **Document**: `spec/v1.0/04-authorization.md`
- **Version**: 1.0.0-draft
- **Status**: Proposal / Working Draft
- **Authority**: [ADR-001](../../docs/adr/0001-govcore-framework-neutral-standard.md)

---

## 1. Scope & Objective

This chapter specifies the normative authorization requirements, policy models, and evaluation guarantees for GovCore-compliant systems. It governs how an `Actor` is evaluated against an `Action` on a `Resource` within a given `Context`.

---

## 2. Authorization Domain Model

```text
 ┌──────────────┐         attempts          ┌────────────┐
 │    ACTOR     │ ────────────────────────> │   ACTION   │
 │ (Claims,     │                           │  (create,  │
 │  Clearance,  │                           │   read,    │
 │  Tenant ID)  │                           │   approve) │
 └──────┬───────┘                           └─────┬──────┘
        │                                         │
        │             ┌────────────────┐          │
        └───────────> │ POLICY ENGINE  │ <────────┘
                      │ (Fail-Closed)  │
                      └───────┬────────┘
                              │
               evaluates with │ on target
                              ▼
                      ┌────────────────┐
                      │    RESOURCE    │
                      │ (Tenant, Type, │
                      │ Classification)│
                      └────────────────┘
                              │
                              ▼
                      ┌────────────────┐
                      │ ACCESS DECISION│
                      │ (ALLOW / DENY) │
                      └────────────────┘
```

### 2.1 Core Entities & Value Types
1. **Actor**: The authenticated Subject acting within an active Tenant with resolved operational claims (roles, clearance level, MFA state).
2. **Action**: The operation being attempted (`create`, `read`, `update`, `delete`, `approve`, `sign`, `export`).
3. **Resource**: The target system entity characterized by:
   - `resource_id`: Unique identifier of the resource.
   - `resource_type`: Qualified domain type (e.g., `permit_application`, `tax_record`).
   - `tenant_id`: Sovereign owner tenant of the resource.
   - `classification`: Security classification (`PUBLIC`, `OFFICIAL`, `CONFIDENTIAL`, `RESTRICTED`).
4. **Context**: Ephemeral operational metadata (network origin, MFA status, current timestamp).
5. **AccessDecision**: The deterministic outcome: `ALLOW` or `DENY`, accompanied by a reason code and evaluated policy identifier.

---

## 3. Normative Evaluation Rules & Invariants

### 3.1 Fail-Closed Default Invariant
An authorization engine MUST default to `DENY` ("fail-closed"). Access SHALL only be granted if at least one applicable policy explicitly yields an `ALLOW` decision and no applicable overriding policy yields a `DENY`.

### 3.2 Tenant Boundary Invariant
An Actor whose active `tenant_id` is $A$ MUST NOT be permitted to perform any action upon a Resource whose `tenant_id` is $B$, unless an explicit, authenticated, and audited cross-tenant delegation policy exists.

### 3.3 Security Classification Invariant
If a Resource has a classification of `CONFIDENTIAL` or `RESTRICTED`, the Actor MUST possess a clearance level equal to or exceeding the resource classification. Failure to meet the clearance level MUST result in an immediate `DENY`.

### 3.4 Multi-Factor Step-Up Invariant
High-privilege actions (e.g., security policy edits, bulk citizen data export, role assignment) MUST require an Actor with verified MFA status (`mfa_verified = True` in current session). If the Actor authenticated without MFA or if the step-up window expired, the Policy Engine MUST yield `DENY` with code `MFA_STEP_UP_REQUIRED`.

---

## 4. Policy Models

Conforming implementations MUST support Role-Based Access Control (RBAC) and SHOULD support Attribute-Based Access Control (ABAC).

### 4.1 Role-Based Access Control (RBAC)
- Permissions are expressed as tuples of `(resource_type, action)` (e.g., `permit:approve`, `document:read`).
- Standard role hierarchies:
  - `SuperAdmin`: Cross-tenant platform maintenance (restricted to global administrative operations).
  - `TenantAdmin`: Administrative governance within a single sovereign Tenant.
  - `Officer`: Operational civil servant executing domain actions.
  - `Auditor`: Read-only access to immutable audit trails and compliance records.
  - `Citizen` / `User`: Scoped access strictly to self-owned records.

### 4.2 Attribute-Based Access Control (ABAC)
Policy evaluation MAY incorporate dynamic contextual attributes:
- Departmental matching: `actor.department == resource.department`.
- Record assignment: `actor.subject_id == resource.assigned_to`.
- Temporal / location constraints: business hours, internal government network ranges.
