"""
Authentication provider abstraction.
Allows pluggable authentication sources without system rewrite.

Current: local (Django)
Future: Keycloak, Azure AD, SAML, generic OAuth2
"""
from abc import ABC, abstractmethod
from typing import Any

from django.contrib.auth import get_user_model

User = get_user_model()


class AuthenticationError(Exception):
    """Base exception for auth failures"""
    pass


class UserNotFoundError(AuthenticationError):
    """User doesn't exist"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Wrong password or credentials"""
    pass


class BaseAuthProvider(ABC):
    """
    Abstract base for auth providers.
    Implement this to add new IdP support.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider (e.g. 'local', 'keycloak')"""
        pass

    @abstractmethod
    def authenticate(self, credentials: dict[str, Any]) -> User:
        """
        Authenticate user with provider-specific credentials.

        Args:
            credentials: Dict with auth details (email, password, token, etc.)

        Returns:
            Authenticated User object

        Raises:
            InvalidCredentialsError if auth fails
            UserNotFoundError if user doesn't exist
        """
        pass

    @abstractmethod
    def create_user(self, user_data: dict[str, Any]) -> User:
        """
        Create new user via this provider.
        Called during initial account provisioning.
        """
        pass

    @abstractmethod
    def sync_user(self, user: User, remote_data: dict[str, Any]) -> User:
        """
        Sync user attributes from remote provider.
        Called periodically or on login for federated updates.
        """
        pass


class LocalAuthProvider(BaseAuthProvider):
    """
    Local authentication provider (embedded Django).
    Users created and authenticated purely within this system.
    """

    @property
    def provider_name(self) -> str:
        return "local"

    def authenticate(self, credentials: dict[str, Any]) -> User:
        """
        Authenticate with email + password.

        Expected credentials:
            {
                'email': 'user@email.com',
                'password': 'secret123',
                'tenant_id': '...'  # optional for multi-tenant
            }
        """
        email = credentials.get("email")
        password = credentials.get("password")

        if not email or not password:
            raise InvalidCredentialsError("Email and password required")

        try:
            user = User.objects.get(email=email, auth_provider="local")
        except User.DoesNotExist as err:
            raise UserNotFoundError(f"User {email} not found") from err

        if not user.is_active:
            raise AuthenticationError(f"User {email} is inactive")

        if not user.check_password(password):
            raise InvalidCredentialsError("Invalid password")

        return user

    def create_user(self, user_data: dict[str, Any]) -> User:
        """
        Create local user with email + password.

        Expected user_data:
            {
                'email': 'user@email.com',
                'password': 'secret123',
                'full_name': 'John Doe',
                'tenant_id': '...',
            }
        """
        email = user_data.get("email")
        password = user_data.get("password")

        if not email or not password:
            raise ValueError("Email and password required")

        if User.objects.filter(email=email).exists():
            raise ValueError(f"User {email} already exists")

        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=user_data.get("full_name", ""),
            tenant_id=user_data.get("tenant_id"),
            auth_provider="local",
        )
        return user

    def sync_user(self, user: User, remote_data: dict[str, Any]) -> User:
        """
        Sync is no-op for local provider (no remote source).
        """
        return user


class OAuthProvider(BaseAuthProvider):
    """
    Generic OAuth2 provider (placeholder for future integration).
    Can be extended for Keycloak, Azure AD, etc.
    """

    @property
    def provider_name(self) -> str:
        return "oauth2"

    def authenticate(self, credentials: dict[str, Any]) -> User:
        raise NotImplementedError("OAuth2 auth not yet implemented")

    def create_user(self, user_data: dict[str, Any]) -> User:
        raise NotImplementedError("OAuth2 user creation not yet implemented")

    def sync_user(self, user: User, remote_data: dict[str, Any]) -> User:
        raise NotImplementedError("OAuth2 sync not yet implemented")


class ProviderRegistry:
    """
    Registry of available auth providers.
    Manages provider lookup and instantiation.
    """

    def __init__(self):
        self._providers = {}
        self._register_default_providers()

    def _register_default_providers(self):
        """Register built-in providers"""
        self.register("local", LocalAuthProvider())
        self.register("oauth2", OAuthProvider())

    def register(self, name: str, provider: BaseAuthProvider):
        """Register a new auth provider"""
        self._providers[name] = provider

    def get(self, name: str) -> BaseAuthProvider | None:
        """Get provider by name"""
        return self._providers.get(name)

    def authenticate(self, provider: str, credentials: dict[str, Any]) -> User:
        """Authenticate using specified provider"""
        auth_provider = self.get(provider)
        if not auth_provider:
            raise ValueError(f"Unknown provider: {provider}")
        return auth_provider.authenticate(credentials)

    def create_user(self, provider: str, user_data: dict[str, Any]) -> User:
        """Create user via specified provider"""
        auth_provider = self.get(provider)
        if not auth_provider:
            raise ValueError(f"Unknown provider: {provider}")
        return auth_provider.create_user(user_data)


# Global registry instance
default_registry = ProviderRegistry()
