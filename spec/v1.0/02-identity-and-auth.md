# GovCore Specification v1.0 — Chapter 2: Identity, Credentials & Authentication

- **Document**: `spec/v1.0/02-identity-and-auth.md`
- **Version**: 1.0.0-draft
- **Status**: Proposal / Working Draft
- **Authority**: [ADR-001](../../docs/adr/0001-govcore-framework-neutral-standard.md)

---

## 1. Scope & Objective

This chapter specifies the normative security requirements and behavioral contracts for **Identity Management, Credential Storage, Multi-Factor Authentication (MFA), and Session Governance** in GovCore-compliant public-sector applications.

---

## 2. Identity Lifecycle State Machine

A conforming system MUST enforce the following deterministic state machine for every `Subject` / `Identity`:

```text
                  ┌──────────────────────┐
                  │ PENDING_VERIFICATION │
                  └──────────┬───────────┘
                             │ email/admin verified
                             ▼
┌──────────────┐  admin/idp  ┌──────────────┐  failed logins   ┌──────────────┐
│  SUSPENDED   │ ──────────> │    ACTIVE    │ ───────────────> │    LOCKED    │
│ (Regulatory) │ <────────── │  (Can Auth)  │ <─────────────── │  (Temporary) │
└──────────────┘             └──────┬───────┘    lockout expires
       │                            │            or admin reset
       │ statutory archival         │ statutory retention end
       ▼                            ▼
┌───────────────────────────────────────────┐
│                TOMBSTONED                 │
│  (Redacted PII, Retained Audit Identifier)│
└───────────────────────────────────────────┘
```

### 2.1 State Definitions & Invariants
1. **`PENDING_VERIFICATION`**: Created but unverified. MUST NOT be permitted to authenticate or obtain operational sessions.
2. **`ACTIVE`**: Fully verified. Allowed to authenticate and establish active sessions subject to credential and policy checks.
3. **`LOCKED`**: Temporarily barred due to suspicious activity or excessive failed authentication attempts. Active sessions SHOULD be immediately terminated.
4. **`SUSPENDED`**: Administratively or regulatorily disabled. All active sessions MUST be immediately terminated. No authentication attempts SHALL succeed.
5. **`TOMBSTONED`**: Permanently retired. In accordance with public records laws and data minimization principles:
   - Personally Identifiable Information (PII) MUST be redacted or anonymized.
   - The canonical `subject_id` MUST be preserved in perpetuity to maintain the cryptographic integrity of past audit logs.

---

## 3. Credential Storage & Cryptographic Requirements

### 3.1 Passwords
1. **Storage Algorithm**: Passwords MUST be hashed using **Argon2id** (RFC 9106).
   - **Minimum Recommended Parameters**:
     - Memory cost ($m$): $\ge 64\,\text{MiB}$ ($65536\,\text{KiB}$)
     - Time cost ($t$): $\ge 3$ iterations
     - Parallelism ($p$): $\ge 1$ thread/lane
2. **Legacy Migration**: Systems migrating from existing databases MAY verify legacy hashes (e.g., PBKDF2-SHA256 with $\ge 600{,}000$ iterations), but MUST automatically re-hash and upgrade the credential to Argon2id upon the user's next successful authentication.
3. **Timing Invariance**: Password verification routines MUST execute in constant time relative to credential validity to prevent user enumeration and timing side-channel attacks.

### 3.2 Password Complexity & Entropy
- Passwords MUST be at least 12 characters in length for general users, and at least 16 characters for administrative/privileged accounts.
- Systems MUST reject passwords found in known breach corpora (e.g., HaveIBeenPwned Top 100k or equivalent government blocklists).
- Arbitrary composition rules (e.g., forcing special character churn every 30 days) SHOULD NOT be enforced, following modern NIST SP 800-63B guidance.

---

## 4. Multi-Factor Authentication (MFA)

### 4.1 Requirement Levels
- All administrative, privileged, and officer roles MUST require MFA.
- Tenancy policies MAY enforce mandatory MFA for all subjects within a tenant.

### 4.2 Supported Factors
1. **Time-Based One-Time Password (TOTP)**:
   - Conforming implementations MUST adhere to [RFC 6238](https://www.ietf.org/rfc/rfc6238.txt).
   - Timestep window MUST be 30 seconds.
   - Allowed drift tolerance MUST NOT exceed $\pm 1$ timestep window (30 seconds before/after).
   - Once used, a TOTP code MUST be marked consumed for that timestep window to prevent replay attacks.
   - TOTP secret seeds MUST be stored encrypted at rest using authenticated symmetric encryption (AES-256-GCM or ChaCha20-Poly1305).
2. **FIDO2 / WebAuthn**:
   - Systems SHOULD support WebAuthn / Passkeys as a phishing-resistant second factor or primary passwordless authenticator.
3. **Backup Recovery Codes**:
   - Implementations supporting MFA MUST provide single-use backup recovery codes.
   - Recovery codes MUST be generated using cryptographically secure random bytes (CSPRNG) with at least 80 bits of entropy.
   - Recovery codes MUST be stored hashed (Argon2id or SHA-256 with per-user salt); plaintext recovery codes MUST only be shown to the user once upon generation.
   - Each recovery code MUST be permanently invalidated immediately upon single use.

---

## 5. Session Governance & Token Lifecycles

### 5.1 Web Sessions & Refresh Tokens
1. **Absolute Timeout**:
   - For privileged / administrator sessions, the absolute session lifetime MUST NOT exceed **12 hours**, regardless of activity.
   - For citizen / standard sessions, the absolute lifetime MUST NOT exceed **24 hours**.
2. **Idle Timeout**:
   - For privileged / administrator sessions, sessions MUST expire after no more than **30 minutes** of inactivity.
   - For standard sessions, sessions SHOULD expire after no more than **60 minutes** of inactivity.
3. **Immediate Invalidation (Revocation Invariants)**:
   A Subject's active sessions and issued tokens MUST be immediately terminated upon:
   - Explicit user sign-out (`LOGOUT`).
   - Credential modification (password reset or MFA modification).
   - Administrative suspension, lockout, or role revocation.
   - Detection of concurrent session anomalies violating tenant policy.
4. **Step-Up Re-Authentication**:
   Sensitive operations (e.g., modifying security credentials, exporting personal records, transferring funds, changing tenant configuration) MUST require re-authentication (prompting for primary credential and/or MFA challenge) if the current session was authenticated more than 10 minutes prior.

---

## 6. External Identity Providers & Federation

Conforming systems MUST support delegating authentication to external sovereign IdPs (e.g., SAML 2.0, OpenID Connect, eIDAS, Keycloak, Azure AD Gov).

### 6.1 Federation Invariants
1. **Immutable Binding**: An external identity link MUST be bound to a tuple of `(idp_issuer, external_subject_id)`.
2. **Tenant Scoping**: External IdP connections MUST be configurable per Tenant to permit tenant-sovereign IdP federations.
3. **Attribute Mapping & Just-In-Time (JIT) Provisioning**:
   - Adapters MUST provide configurable attribute mapping for claims (email, legal name, organization unit, national identity token).
   - JIT provisioning of new Subjects upon IdP callback MUST respect the target Tenant's registration policies.

---

## 7. Threat Mitigation & Brute-Force Defense

1. **Account Lockout**:
   - After a maximum of **5 consecutive failed authentication attempts** within a 15-minute sliding window, the system MUST lock the account or impose progressive exponential delays.
   - Lockout duration SHOULD default to **15 minutes** before automated reset, or require administrator intervention for privileged accounts.
2. **Rate Limiting**:
   - Authentication endpoints MUST be rate-limited by originating client IP address (e.g., max 10 requests per minute per IP).
3. **Information Disclosure Prevention**:
   - Authentication failure responses MUST NOT indicate whether the failure was due to an unknown username versus an invalid password. The response MUST be a generic failure message.

---

## 8. Audit Attribution Requirements

Every authentication event MUST produce an immutable `AuditEvent` conforming to Chapter 5, recording:
- `action`: `AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILURE`, `AUTH_LOGOUT`, `AUTH_MFA_CHALLENGE`, `AUTH_MFA_FAILURE`, `AUTH_PASSWORD_RESET`, `AUTH_ACCOUNT_LOCKED`.
- `actor`: Resolved `Actor` or `AnonymousSubject` (for failed attempts with attempted username masked or hashed).
- `tenant_id`: Resolved tenant context.
- `metadata`: Client IP, User-Agent, Authentication Method (Password, TOTP, WebAuthn, OIDC), failure reason code.
