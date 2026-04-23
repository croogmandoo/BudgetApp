"""Django admin for identity models.

Household, User, and APIToken are registered so an admin can inspect and
repair auth state during dev and after-hours incident response. The user
form is Django's stock UserAdmin extended with our household/role fields;
password hashing still runs through Argon2 via PASSWORD_HASHERS.

APIToken rows only carry the hash of the token — the plaintext is shown
to the user once on creation. Admin can revoke (clear a row) but cannot
read the secret, which matches SPEC §7.1.
"""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import APIToken, Household, User


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("name", "base_currency", "created_at")
    search_fields = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        *(DjangoUserAdmin.fieldsets or ()),
        ("Household", {"fields": ("household", "role", "totp_enforced_at", "disabled_at")}),
    )
    add_fieldsets = (
        *(DjangoUserAdmin.add_fieldsets or ()),
        ("Household", {"fields": ("household", "role")}),
    )
    list_display = ("username", "email", "household", "role", "totp_enforced_at", "is_staff")
    list_filter = ("role", "household", "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name")


@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "last_used_at", "revoked_at", "created_at")
    list_filter = ("revoked_at",)
    search_fields = ("name", "user__username", "user__email")
    readonly_fields = ("id", "token_hash", "last_used_at", "created_at", "updated_at")

    def has_add_permission(self, request: object) -> bool:
        # Tokens must be minted by the API (which hashes the plaintext and
        # shows it to the caller once). The admin form has no way to surface
        # the plaintext, so adding here would produce a useless row.
        return False
