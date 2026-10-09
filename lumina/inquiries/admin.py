# inquiries/admin.py
# Registers the contact-form messages so staff can read and answer them.

from django.contrib import admin
from django.utils import timezone

from .models import Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "status", "created_at", "answered_at")
    list_filter = ("status", "subject", "created_at")
    list_editable = ("status",)
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "subject", "message", "user", "created_at")
    date_hierarchy = "created_at"
    actions = ["mark_answered"]

    @admin.action(description="Mark selected inquiries as answered")
    def mark_answered(self, request, queryset):
        updated = queryset.update(status="answered", answered_at=timezone.now())
        self.message_user(request, f"{updated} inquiry(ies) marked as answered.")