import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with multi-tenant support and pluggable auth providers.

    Design decisions:
    - UUID primary key for distributed systems
    - tenant_id ensures multi-tenant isolation
    - auth_provider allows future IdP swaps (local → Keycloak → Azure AD)
    - is_active enables soft delete patterns
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Multi-tenant
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Core identity
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)

    # Authentication provider (local, keycloak, azure, etc.)
    # Allows future migration without system rewrite
    AUTH_PROVIDER_CHOICES = [
        ("local", "Local (embedded Django)"),
        ("keycloak", "Keycloak"),
        ("azure_ad", "Azure AD / Entra ID"),
        ("saml", "SAML 2.0"),
        ("oauth2", "Generic OAuth2"),
    ]
    auth_provider = models.CharField(
        max_length=50,
        choices=AUTH_PROVIDER_CHOICES,
        default="local",
        help_text="Authentication provider for this user",
    )

    # Account status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # MFA requirement
    mfa_required = models.BooleanField(default=True)
    mfa_enabled = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = "users_user"
        indexes = [
            models.Index(fields=["tenant_id", "email"]),
            models.Index(fields=["auth_provider"]),
        ]

