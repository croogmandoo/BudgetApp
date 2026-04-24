"""HTTP views for ``apps.accounts``.

Scope: login, logout, TOTP enrolment + verification, password changes,
household membership management, personal-access-token CRUD.
"""

from __future__ import annotations

import base64
import binascii

import django_otp
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import TOTPDeviceSecret, User
from apps.accounts.serializers import (
    HouseholdSerializer,
    LoginSerializer,
    UserSerializer,
)
from apps.core.crypto import WrappedDEK, get_cipher


def _device_plaintext_key(device: TOTPDevice) -> str:
    """Return the plaintext hex TOTP key for *device*, decrypting if necessary.

    If no TOTPDeviceSecret exists (encryption was skipped — e.g. in dev without
    APP_MASTER_KEY) the raw device.key is returned unchanged.
    """
    cipher = get_cipher()
    if cipher is None:
        return device.key
    try:
        secret = device.secret  # type: ignore[attr-defined]
    except TOTPDeviceSecret.DoesNotExist:
        return device.key
    dek = cipher.unwrap_dek(WrappedDEK.from_bytes(bytes(secret.wrapped_dek)))
    return cipher.decrypt(bytes(secret.ciphertext), bytes(secret.nonce), dek).decode()


class _CsrfEnforcedAnonAuth(SessionAuthentication):
    """Run CSRF check without rejecting unauthenticated requests."""

    def authenticate(self, request: Request) -> None:
        self.enforce_csrf(request)


# Computed once at module load; used only to equalise timing on unknown email.
_DUMMY_HASH: str = make_password("dummy-constant-value")


def _user_data(user: User, request: Request) -> dict:
    """Serialize a user for API responses."""
    return UserSerializer(user, context={"request": request}).data


def _household_data(user: User) -> dict | None:
    """Serialize the user's household, or None if not assigned."""
    if user.household_id is None:
        return None
    return HouseholdSerializer(user.household).data


def _authenticate_user(email: str, password: str) -> tuple[User | None, Response | None]:
    """Look up user by email and verify password.

    Returns ``(user, None)`` on success or ``(None, error_response)`` on failure.
    Centralises the two "invalid credentials" branches so LoginView.post stays
    under the PLR0911 return-statement limit.
    """
    _bad = Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        check_password(password, _DUMMY_HASH)  # equalise Argon2 timing
        return None, _bad
    if not user.check_password(password):
        return None, _bad
    if user.disabled_at is not None:
        return None, Response({"detail": "Account is disabled."}, status=status.HTTP_403_FORBIDDEN)
    return user, None


class LoginView(APIView):
    """POST /api/v1/auth/login/

    Authenticates via email + password, then checks TOTP enrollment state.

    - Not enrolled → session started, returns totp_enrollment_required=true.
    - Enrolled + valid token → session started + OTP verified, returns full response.
    - Enrolled + missing/invalid token → 401.
    """

    authentication_classes = [_CsrfEnforcedAnonAuth]
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email: str = serializer.validated_data["email"]
        password: str = serializer.validated_data["password"]
        totp_token: str = serializer.validated_data.get("totp_token", "")

        user, err = _authenticate_user(email, password)
        if err is not None:
            return err

        # Not enrolled → allow partial login so the user can complete enrollment.
        # Check confirmed device presence, not totp_enforced_at, so the two
        # facts stay decoupled (admin-created users may lack a device even if
        # totp_enforced_at were somehow set, or vice-versa).
        has_confirmed_device = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
        if not has_confirmed_device:
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return Response(
                {
                    "totp_enrollment_required": True,
                    "user": _user_data(user, request),
                },
                status=status.HTTP_200_OK,
            )

        # Enrolled → require and verify the TOTP token.
        # Decrypt each device's key in-memory before verification so the
        # plaintext key is never read from the DB column (SPEC §7.2).
        verified_device = None
        for d in django_otp.devices_for_user(user, confirmed=True):
            d.key = _device_plaintext_key(d)
            if d.verify_token(totp_token):
                verified_device = d
                break
        if verified_device is None:
            return Response(
                {"detail": "Invalid authenticator code."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        django_otp.login(request, verified_device)

        return Response(
            {
                "totp_enrollment_required": False,
                "user": _user_data(user, request),
                "household": _household_data(user),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """POST /api/v1/auth/logout/

    Ends the current session. Returns 204.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /api/v1/auth/me/

    Returns the currently authenticated user and their household.
    Also surfaces ``totp_verified`` so the SPA knows whether the
    session is partial (password only) or fully authenticated.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user: User = request.user  # type: ignore[assignment]
        return Response(
            {
                "user": _user_data(user, request),
                "household": _household_data(user),
            },
            status=status.HTTP_200_OK,
        )


class TOTPEnrollView(APIView):
    """POST /api/v1/auth/totp/enroll/

    Creates a new unconfirmed TOTP device for the authenticated user and
    returns the provisioning URI + base32 secret so an authenticator app
    can scan the QR code.

    Safe to call repeatedly — any existing unconfirmed device is replaced.
    Requires an active session (even a partial one from password-only login).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        user: User = request.user  # type: ignore[assignment]

        # Replace any stale unconfirmed device so enroll is idempotent.
        TOTPDevice.objects.filter(user=user, confirmed=False).delete()

        device = TOTPDevice.objects.create(user=user, name="default", confirmed=False)
        plaintext_key = device.key  # lowercase hex string generated by django-otp

        cipher = get_cipher()
        if cipher is not None:
            dek = cipher.generate_dek()
            wrapped = cipher.wrap_dek(dek)
            ciphertext, nonce = cipher.encrypt(plaintext_key.encode(), dek)
            TOTPDeviceSecret.objects.create(
                device=device,
                wrapped_dek=wrapped.to_bytes(),
                ciphertext=ciphertext,
                nonce=nonce,
            )
            # Replace the plaintext key in the DB with a dummy so a database
            # dump never exposes the TOTP secret (SPEC §7.2).
            device.key = "00"
            device.save(update_fields=["key"])

        # django-otp stores the key as a lowercase hex string; convert to base32
        # so authenticator apps can consume it.
        secret_b32 = base64.b32encode(binascii.unhexlify(plaintext_key)).decode()
        otpauth_uri = f"otpauth://totp/BudgetApp:{user.email}?secret={secret_b32}&issuer=BudgetApp"

        return Response(
            {"secret": secret_b32, "otpauth_uri": otpauth_uri},
            status=status.HTTP_200_OK,
        )


class TOTPConfirmView(APIView):
    """POST /api/v1/auth/totp/confirm/

    Verifies the first TOTP code from the user's authenticator app, marks the
    device confirmed, and records ``totp_enforced_at`` on the user model.

    Request body: ``{"totp_token": "123456"}``
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        user: User = request.user  # type: ignore[assignment]
        totp_token = request.data.get("totp_token", "")

        device = TOTPDevice.objects.filter(user=user, confirmed=False).order_by("-id").first()
        if device is None:
            return Response(
                {"detail": "No pending TOTP enrollment found. Call /totp/enroll/ first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device.key = _device_plaintext_key(device)
        if not device.verify_token(totp_token):
            return Response(
                {"detail": "Invalid code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device.confirmed = True
        device.save()

        user.totp_enforced_at = timezone.now()
        user.save(update_fields=["totp_enforced_at"])

        django_otp.login(request, device)

        return Response(
            {"detail": "TOTP enrollment complete."},
            status=status.HTTP_200_OK,
        )
