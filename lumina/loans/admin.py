# loans/admin.py
# Admin screen for issuing and returning physical books.

from django.contrib import admin
from django.utils import timezone

from .models import BookIssue


class OverdueFilter(admin.SimpleListFilter):
    """Sidebar filter: show only books that are late."""
    title = "overdue"
    parameter_name = "overdue"

    def lookups(self, request, model_admin):
        return (("yes", "Overdue"), ("no", "Not overdue"))

    def queryset(self, request, queryset):
        late = dict(status=BookIssue.Status.ISSUED, due_date__lt=timezone.localdate())
        if self.value() == "yes":
            return queryset.filter(**late)
        if self.value() == "no":
            return queryset.exclude(**late)
        return queryset


@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = (
        "copy", "user", "issued_at", "due_date",
        "returned_at", "loan_status", "issued_by",
    )
    list_filter = ("status", OverdueFilter, "due_date")
    search_fields = (
        "user__email", "user__first_name", "user__last_name",
        "copy__inventory_code", "copy__book__title",
    )
    autocomplete_fields = ("user", "copy")
    date_hierarchy = "issued_at"
    actions = ["mark_returned"]

    # Status is only changed by the "Mark returned" action; staff is set automatically
    readonly_fields = ("issued_at", "returned_at", "status", "issued_by")

    @admin.display(description="Status")
    def loan_status(self, obj):
        return obj.display_status          # shows "Overdue" for late books

    def get_readonly_fields(self, request, obj=None):
        # After a loan exists, the borrower and copy are locked
        if obj:
            return self.readonly_fields + ("user", "copy")
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:
            obj.issued_by = request.user   # whoever is logged in issued the book
        super().save_model(request, obj, form, change)

    @admin.action(description="Mark selected loans as returned")
    def mark_returned(self, request, queryset):
        count = 0
        for issue in queryset.filter(status=BookIssue.Status.ISSUED):
            issue.mark_returned()
            count += 1
        self.message_user(request, f"{count} loan(s) marked as returned.")