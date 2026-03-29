"""
Core identity module: Authentication, authorization, MFA, and provider management.

Designed to be future-proof for IdP migration (Keycloak, Azure AD, etc.).
Separation of concerns:
  - Authentication (who the user is)
  - Authorization (what they can do) [separate in core.access]
  - MFA (second factor)
  - Providers (pluggable auth sources)
"""
