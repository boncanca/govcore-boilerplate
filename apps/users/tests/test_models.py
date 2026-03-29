import uuid

import pytest

from apps.users.models import User


@pytest.mark.django_db
def test_create_user_with_email_and_password():
    user = User.objects.create_user(email="user@example.com", password="safe-pass-123")

    assert user.email == "user@example.com"
    assert user.check_password("safe-pass-123")
    assert user.auth_provider == "local"


@pytest.mark.django_db
def test_create_superuser_sets_flags():
    admin_user = User.objects.create_superuser(email="admin@example.com", password="safe-pass-123")

    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True


@pytest.mark.django_db
def test_tenant_id_accepts_uuid():
    tenant_id = uuid.uuid4()
    user = User.objects.create_user(email="tenant@example.com", password="safe-pass-123", tenant_id=tenant_id)

    assert user.tenant_id == tenant_id
