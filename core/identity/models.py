"""
Identity models: MFA devices, external identities, and audit records.
Designed for government-grade security with multi-factor authentication.
"""
import secrets
import uuid

import pyotp
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class MFADevice(models.Model):
    """
    Multi-factor authentication devices (TOTP, backup codes, etc).
    Supports multiple MFA methods per user for recovery scenarios.
    """
    MFA_DEVICE_TYPES = [
        ("totp", "Time-based One-Time Password (Google Authenticator)"),
        ("sms", "SMS-based OTP"),
        ("email", "Email-based OTP"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mfa_devices")

    device_type = models.CharField(max_length=50, choices=MFA_DEVICE_TYPES)
    name = models.CharField(max_length=255, help_text="User-friendly name (e.g. 'Main phone')")

    # TOTP secret (encrypted in production)
    totp_secret = models.CharField(max_length=32, null=True, blank=True)

    # Confirmed = user has verified this device works
    is_primary = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)

    # Track last used for recovery/anomaly detection
    last_used = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "identity_mfa_device"
        unique_together = [["user", "name"]]
        ordering = ["-is_primary", "-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.name}"

    def get_totp_provisioning_uri(self, issuer: str = "Government ERP"):
        """Generate URI for QR code provisioning"""
        if self.totp_secret:
            totp = pyotp.TOTP(self.totp_secret)
            return totp.provisioning_uri(
                name=self.user.email,
                issuer_name=issuer
            )
        return None

    def verify_totp(self, token: str) -> bool:
        """Verify TOTP token (with 30-second grace window)"""
        if not self.totp_secret:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)  # ±30 seconds


class MFABackupCode(models.Model):
    """
    Backup codes for account recovery (when primary MFA is unavailable).
    Generated as one-time-use codes for gov-grade security.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mfa_backup_codes")

    # Hashed code (never store plaintext)
    code_hash = models.CharField(max_length=255)

    # One-time use
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_mfa_backup_code"
        ordering = ["created_at"]

    @staticmethod
    def generate_codes(count: int = 10) -> list[str]:
        """Generate readable backup codes (format: XXXX-XXXX-XXXX)"""
        codes = []
        for _ in range(count):
            # Generate 12 random characters (96 bits entropy)
            code = secrets.token_hex(6).upper()  # 12 hex chars
            formatted = f"{code[:4]}-{code[4:8]}-{code[8:]}"
            codes.append(formatted)
        return codes


class ExternalIdentity(models.Model):
    """
    Maps users to external identity providers (future IdP migration).

    Enables:
    - Keycloak/Azure AD linking
    - Multiple identities per user
    - Smooth provider transitions

    Example:
      User 1 (local) → ExternalIdentity(provider='azure', external_id='user@ministry.gov')
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="external_identities")

    # IdP details
    provider = models.CharField(max_length=50, db_index=True)  # keycloak, azure, saml, etc.
    external_id = models.CharField(max_length=255)  # User ID in external system

    # Metadata (provider-specific claims)
    metadata = models.JSONField(default=dict, blank=True)

    # Linked (when this external account was connected)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_sync = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "identity_external_identity"
        unique_together = [["provider", "external_id"]]
        indexes = [
            models.Index(fields=["user", "provider"]),
            models.Index(fields=["provider", "external_id"]),
        ]

    def __str__(self):
        return f"{self.user.email} @ {self.provider}"


class LoginAudit(models.Model):
    """
    Audit trail for all login attempts (successful and failed).
    Critical for government compliance and security investigations.
    """
    LOGIN_RESULT_CHOICES = [
        ("success", "Successful login"),
        ("failed_password", "Failed - incorrect password"),
        ("failed_mfa", "Failed - MFA verification failed"),
        ("failed_inactive", "Failed - account inactive"),
        ("failed_not_found", "Failed - user not found"),
        ("blocked", "Blocked - too many attempts"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="login_audits")

    # Who tried to login (might not be registered user)
    attempted_email = models.EmailField()

    # Result of attempt
    result = models.CharField(max_length=50, choices=LOGIN_RESULT_CHOICES)

    # Client info (for anomaly detection)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "identity_login_audit"
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["attempted_email", "timestamp"]),
            models.Index(fields=["result", "timestamp"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.attempted_email} - {self.result} @ {self.timestamp}"
