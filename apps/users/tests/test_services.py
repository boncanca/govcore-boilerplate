import pytest

from apps.users.models import User
from core.identity.models import ExternalIdentity, LoginAudit


@pytest.mark.django_db
def test_external_identity_can_be_linked():
    user = User.objects.create_user(email="identity@example.com", password="safe-pass-123")

    external = ExternalIdentity.objects.create(
        user=user,
        provider="keycloak",
        external_id="external-123",
    )

    assert external.user_id == user.id
    assert external.provider == "keycloak"


@pytest.mark.django_db
def test_login_audit_record_can_be_created():
    user = User.objects.create_user(email="audit@example.com", password="safe-pass-123")

    audit = LoginAudit.objects.create(
        user=user,
        attempted_email=user.email,
        result="success",
    )

    assert audit.result == "success"
    assert audit.attempted_email == user.email
