# accounts/admin.py
# Registers the custom User model in Django's admin site.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin screen for library members (email is the login, not a username)."""

    model = User

    # Columns shown in the member list
    list_display = (
        "email", "first_name", "last_name", "role",
        "is_blocked", "is_active", "is_staff", "date_joined",
    )
    list_filter = ("role", "is_blocked", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name", "phone")
    ordering = ("-date_joined",)
    readonly_fields = ("last_login", "date_joined")

    # Layout of the "edit user" page
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone", "role")}),
        ("Account status", {"fields": ("is_active", "is_blocked")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # Layout of the "add user" page (the password is typed twice)
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "role", "password1", "password2"),
        }),
    )

    # Bulk actions in the dropdown above the list
    actions = ["block_users", "unblock_users"]

    @admin.action(description="Block selected members")
    def block_users(self, request, queryset):
        updated = queryset.update(is_blocked=True)
        self.message_user(request, f"{updated} member(s) blocked.")

    @admin.action(description="Unblock selected members")
    def unblock_users(self, request, queryset):
        updated = queryset.update(is_blocked=False)
        self.message_user(request, f"{updated} member(s) unblocked.")