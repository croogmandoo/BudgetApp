"""Identity models: ``Household``, ``User``, ``APIToken``.

See SPEC §6 (data model) and §7.1 (auth). Key invariants encoded here:

    - Every user belongs to exactly one household; data visibility is
      household-wide (SPEC §0, §7.1).
    - Roles are ``admin`` / ``member`` / ``viewer``.
    - TOTP is mandatory. ``User.totp_enforced_at`` records when the user
      completed enrolment; login flows must refuse a user whose
      ``totp_enforced_at`` is null.
    - API tokens are stored as hashes only. Scopes are a JSON list of
      strings like ``"transactions:read"``.
"""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.core.models import TimestampedModel


class Household(TimestampedModel):
    """A household tenant. One instance per deployment in v1 (SPEC §7.1)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    base_currency = models.CharField(max_length=3, default="CAD")


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    VIEWER = "viewer", "Viewer"


class User(AbstractUser):
    """Custom user bound to a household with a role and mandatory TOTP.

    We subclass ``AbstractUser`` (not ``AbstractBaseUser``) because Django's
    built-in fields cover everything we need and keep admin integrations
    trivial. The primary key is a UUID for API stability.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    household = models.ForeignKey(
        Household,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
    )
    role = models.CharField(
        max_length=16,
        choices=UserRole.choices,
        default=UserRole.MEMBER,
    )
    # NULL until the user finishes TOTP enrolment. Auth flows must block
    # login for users where this is NULL (SPEC §7.1).
    totp_enforced_at = models.DateTimeField(null=True, blank=True)
    disabled_at = models.DateTimeField(null=True, blank=True)


class APIToken(TimestampedModel):
    """Personal access token for API clients.

    Only the hash of the token is persisted; the plaintext is shown to the
    user exactly once on creation. Scopes follow the ``<resource>:<verb>``
    convention (e.g. ``transactions:read``) — see SPEC §5.1.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_tokens")
    name = models.CharField(max_length=128)
    token_hash = models.CharField(max_length=128, unique=True)
    scopes = models.JSONField(default=list)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "revoked_at"]),
        ]


class TOTPDeviceSecret(models.Model):
    """Envelope-encrypted TOTP secret for a TOTPDevice (SPEC §7.2).

    When APP_MASTER_KEY is set, the plaintext ``device.key`` is replaced with
    a dummy value and the real key is stored here, encrypted under a per-row
    DEK that is itself wrapped by the master key.

    Wire layout mirrors WrappedDEK: ``wrapped_dek`` = nonce||ciphertext of the
    DEK; ``nonce`` + ``ciphertext`` are the GCM nonce and ciphertext of the
    plaintext TOTP hex key.
    """

    device = models.OneToOneField(TOTPDevice, on_delete=models.CASCADE, related_name="secret")
    wrapped_dek = models.BinaryField()
    ciphertext = models.BinaryField()
    nonce = models.BinaryField()

    class Meta:
        app_label = "accounts"

    def __str__(self) -> str:
        return f"TOTPDeviceSecret(device_id={self.device_id})"
