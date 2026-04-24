"""DRF serializers for ``apps.accounts``.

Scope: serializers for Household, User (admin + self views are different),
TOTP enrolment payloads, and APIToken issuance / listing / revocation.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import Household, User


class HouseholdSerializer(serializers.ModelSerializer):
    """Read-only household representation surfaced on login + /me."""

    class Meta:
        model = Household
        fields = ["id", "name", "base_currency"]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """Read-only user representation surfaced on login + /me.

    ``totp_verified`` is a transient flag sourced from the OTP middleware;
    it is not stored on the model but is injected by views that have
    access to the request.
    """

    household_id = serializers.UUIDField(read_only=True)
    totp_verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "role", "household_id", "totp_verified"]
        read_only_fields = fields

    def get_totp_verified(self, obj: User) -> bool:
        """Return True if the OTP middleware has marked the session verified."""
        request = self.context.get("request")
        if request is None:
            return False
        # django_otp sets request.user.is_verified() when a device is verified.
        try:
            return bool(obj.is_verified())
        except AttributeError:
            return False


class LoginSerializer(serializers.Serializer):
    """Write-only login payload."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    totp_token = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        write_only=True,
        max_length=16,
    )
