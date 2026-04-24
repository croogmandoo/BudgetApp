"""URL patterns for the auth surface, mounted under ``/api/v1/auth/``."""

from __future__ import annotations

from django.urls import path

from apps.accounts.views import (
    LoginView,
    LogoutView,
    MeView,
    TOTPConfirmView,
    TOTPEnrollView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("totp/enroll/", TOTPEnrollView.as_view(), name="auth-totp-enroll"),
    path("totp/confirm/", TOTPConfirmView.as_view(), name="auth-totp-confirm"),
]
