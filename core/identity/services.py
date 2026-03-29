"""
Authentication service: orchestrates login flow with MFA,provider selection, and audit.
"""
from typing import Any

from django.contrib.auth import get_user_model
from django.utils import timezone

from .mfa.services import MFAService
from .models import ExternalIdentity, LoginAudit
from .providers.base import AuthenticationError, InvalidCredentialsError, UserNotFoundError, default_registry

User = get_user_model()


class MFAChallengeRequiredError(Exception):
    """Raised when MFA verification needed"""
    def __init__(self, user_id: str, mfa_token: str):
        self.user_id = user_id
        self.mfa_token = mfa_token


class AuthenticationService:
    """
    Main authentication orchestrator.
    Handles: provider selection, login, MFA, audit logging.
    """

    @staticmethod
    def login(
        email: str,
        password: str,
        tenant_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User, str]:
        """
        Authenticate user with email + password.
        Returns: (user, session_token)

        Raises:
            MFAChallengeRequiredError if MFA verification needed
            InvalidCredentialsError if credentials wrong
            UserNotFoundError if user doesn't exist
        """
        try:
            # Try to find user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist as err:
                # Log failed attempt
                AuthenticationService._log_login(
                    email, "failed_not_found", ip_address, user_agent
                )
                raise UserNotFoundError(f"User {email} not found") from err

            # Check if inactive
            if not user.is_active:
                AuthenticationService._log_login(
                    email, "failed_inactive", ip_address, user_agent, user
                )
                raise AuthenticationError(f"User {email} is inactive")

            # Authenticate via configured provider
            provider = default_registry.get(user.auth_provider)
            if not provider:
                raise ValueError(f"Unknown auth provider: {user.auth_provider}")

            credentials = {"email": email, "password": password}
            authenticated_user = provider.authenticate(credentials)

            # Update last_login
            authenticated_user.last_login = timezone.now()
            authenticated_user.save()

            # Check if MFA required
            if authenticated_user.mfa_enabled and authenticated_user.mfa_required:
                # Generate temporary MFA challenge token
                mfa_token = __import__('secrets').token_urlsafe(32)

                # Store in cache/session (in production, use Redis)
                # For now, return the user so frontend can request MFA
                AuthenticationService._log_login(
                    email, "success", ip_address, user_agent, authenticated_user
                )
                raise MFAChallengeRequiredError(str(authenticated_user.id), mfa_token)

            # Success
            AuthenticationService._log_login(
                email, "success", ip_address, user_agent, authenticated_user
            )

            # Generate session token (JWT in production)
            session_token = f"session_{authenticated_user.id}"
            return authenticated_user, session_token

        except (AuthenticationError, InvalidCredentialsError, MFAChallengeRequiredError):
            raise
        except Exception:
            AuthenticationService._log_login(
                email, "failed_password", ip_address, user_agent
            )
            raise

    @staticmethod
    def verify_mfa(
        user_id: str,
        mfa_code: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User, str]:
        """
        Verify MFA code and complete login.
        Called after MFAChallengeRequired exception.

        Supports:
        - TOTP codes
        - Backup codes
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist as err:
            raise ValueError(f"User {user_id} not found") from err

        # Try TOTP first
        if MFAService.verify_totp(user, mfa_code):
            AuthenticationService._log_login(
                user.email, "success", ip_address, user_agent, user
            )
            session_token = f"session_{user.id}"
            return user, session_token

        # Try backup code
        if MFAService.verify_backup_code(user, mfa_code):
            AuthenticationService._log_login(
                user.email, "success", ip_address, user_agent, user
            )
            session_token = f"session_{user.id}"
            return user, session_token

        # Failed
        AuthenticationService._log_login(
            user.email, "failed_mfa", ip_address, user_agent, user
        )
        raise AuthenticationError("Invalid MFA code")

    @staticmethod
    def create_user_local(
        email: str,
        password: str,
        full_name: str = "",
        tenant_id: str | None = None,
    ) -> User:
        """
        Create new local user (admin provisioning).
        """
        if User.objects.filter(email=email).exists():
            raise ValueError(f"User {email} already exists")

        user_data = {
            "email": email,
            "password": password,
            "full_name": full_name,
            "tenant_id": tenant_id,
        }

        provider = default_registry.get("local")
        return provider.create_user(user_data)

    @staticmethod
    def link_external_identity(
        user: User,
        provider: str,
        external_id: str,
        metadata: dict[str, Any] = None,
    ) -> ExternalIdentity:
        """
        Link external identity (Keycloak, Azure AD, etc).
        Enables future IdP migration.
        """
        external_identity, created = ExternalIdentity.objects.update_or_create(
            user=user,
            provider=provider,
            defaults={
                "external_id": external_id,
                "metadata": metadata or {},
                "is_active": True,
            }
        )
        return external_identity

    @staticmethod
    def _log_login(
        email: str,
        result: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        user: User | None = None,
    ) -> LoginAudit:
        """Log login attempt for audit trail"""
        return LoginAudit.objects.create(
            user=user,
            attempted_email=email,
            result=result,
            ip_address=ip_address,
            user_agent=user_agent,
        )
