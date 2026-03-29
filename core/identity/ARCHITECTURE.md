# Identity Architecture

## Goal

Provide a reusable identity foundation that is embedded by default and future-ready for external identity providers.

## Core Principles

1. Keep authentication and authorization separate.
2. Keep provider integration pluggable.
3. Keep MFA optional but first-class.

## Components

- User model with `auth_provider` and `tenant_id` fields.
- `ExternalIdentity` mapping table for future IdP links.
- MFA services for TOTP and backup code workflows.
- Provider registry pattern for local and future external auth.

## Future Expansion

- Add provider modules (`keycloak`, `azure_ad`, `saml`) implementing the same provider contract.
- Add API endpoints for login, MFA challenge, and token lifecycle.
- Add policy layer in a separate authorization module.
