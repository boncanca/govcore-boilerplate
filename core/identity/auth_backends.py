"""
Django REST Framework authentication backends using our identity service.
"""
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


class IdentityServiceAuthentication(BaseAuthentication):
    """
    Custom authentication backend that delegates to IdentityService.
    Supports future provider swapping without DRF changes.
    """

    def authenticate(self, request):
        """
        Authenticate request. Currently supports:
        - JWT tokens
        - Session cookies

        Can be extended to support other token types.
        """
        # Check for JWT token
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            return self.authenticate_token(token)

        # Check for session cookie
        if request.user and request.user.is_authenticated:
            return (request.user, None)

        return None

    def authenticate_token(self, token: str):
        """Validate JWT or session token"""
        # This will be implemented with proper JWT validation
        # For now, placeholder
        raise AuthenticationFailed("Invalid token")

    def authenticate_header(self, request):
        """Return WWW-Authenticate header"""
        return "Bearer"
