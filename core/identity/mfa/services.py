"""
MFA services: TOTP management, backup code generation, and verification.
Government-grade multi-factor authentication.
"""
import hashlib
from typing import TYPE_CHECKING

import pyotp
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.identity.models import MFABackupCode, MFADevice

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

User = get_user_model()


class MFAService:
    """Service for managing multi-factor authentication"""

    @staticmethod
    def generate_totp_secret() -> str:
        """Generate a random TOTP secret"""
        return pyotp.random_base32()

    @staticmethod
    def setup_totp(user: "AbstractBaseUser", device_name: str = "Default") -> tuple[str, str | None]:
        """
        Set up TOTP for a user.
        Returns: (secret, provisioning_uri) for QR code
        """
        secret = MFAService.generate_totp_secret()
        device = MFADevice.objects.create(
            user=user,
            device_type="totp",
            name=device_name,
            totp_secret=secret,
        )

        uri = device.get_totp_provisioning_uri()
        return secret, uri

    @staticmethod
    def confirm_totp(user: "AbstractBaseUser", device_name: str, token: str) -> bool:
        """
        Verify user can generate valid TOTP tokens, then confirm device.
        User must provide a valid token before activation.
        """
        try:
            device = MFADevice.objects.get(
                user=user,
                name=device_name,
                device_type="totp",
                is_confirmed=False,
            )
        except MFADevice.DoesNotExist:
            return False

        if device.verify_totp(token):
            device.is_confirmed = True
            if not MFADevice.objects.filter(user=user, is_confirmed=True).exists():
                device.is_primary = True
            device.save()

            # Enable MFA on user
            user.mfa_enabled = True
            user.save()
            return True

        return False

    @staticmethod
    def verify_totp(user: "AbstractBaseUser", token: str) -> bool:
        """Verify a TOTP token against user's devices"""
        devices = MFADevice.objects.filter(
            user=user,
            device_type="totp",
            is_confirmed=True,
        )

        for device in devices:
            if device.verify_totp(token):
                device.last_used = timezone.now()
                device.save()
                return True

        return False

    @staticmethod
    def generate_backup_codes(user: "AbstractBaseUser", count: int = 10) -> list[str]:
        """
        Generate one-time backup codes for account recovery.
        Returns plaintext codes (only shown once to user).
        """
        # Remove old unused codes
        MFABackupCode.objects.filter(user=user, is_used=False).delete()

        # Generate new codes
        codes = MFABackupCode.generate_codes(count)

        # Store hashed versions
        for code in codes:
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            MFABackupCode.objects.create(user=user, code_hash=code_hash)

        return codes

    @staticmethod
    def verify_backup_code(user: "AbstractBaseUser", code: str) -> bool:
        """Verify and consume a backup code (one-time use)"""
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        try:
            backup_code = MFABackupCode.objects.get(
                user=user,
                code_hash=code_hash,
                is_used=False,
            )
        except MFABackupCode.DoesNotExist:
            return False

        # Mark as used
        backup_code.is_used = True
        backup_code.used_at = timezone.now()
        backup_code.save()

        return True

    @staticmethod
    def disable_mfa(user: "AbstractBaseUser") -> None:
        """Disable MFA for user (removes all devices and codes)"""
        MFADevice.objects.filter(user=user).delete()
        MFABackupCode.objects.filter(user=user).delete()
        user.mfa_enabled = False
        user.save()

    @staticmethod
    def list_devices(user: "AbstractBaseUser") -> list[MFADevice]:
        """List all MFA devices for user"""
        return MFADevice.objects.filter(user=user).order_by("-is_primary", "-created_at")

    @staticmethod
    def remove_device(user: "AbstractBaseUser", device_id: str) -> bool:
        """Remove an MFA device"""
        try:
            device = MFADevice.objects.get(id=device_id, user=user)
            device.delete()

            # If primary device removed, set new one
            if device.is_primary:
                other_devices = MFADevice.objects.filter(user=user, is_confirmed=True).first()
                if other_devices:
                    other_devices.is_primary = True
                    other_devices.save()
                else:
                    # No confirmed devices left, disable MFA
                    user.mfa_enabled = False
                    user.save()

            return True
        except MFADevice.DoesNotExist:
            return False
