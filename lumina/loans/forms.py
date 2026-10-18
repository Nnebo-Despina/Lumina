# loans/forms.py

from datetime import timedelta

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from catalogue.models import BookCopy
from lumina.formutils import AdminFormMixin

from .models import BookIssue

User = get_user_model()


class BookIssueForm(AdminFormMixin, forms.ModelForm):
    """Issue a physical copy to a member (administrator only)."""

    class Meta:
        model = BookIssue
        fields = ["user", "copy", "due_date", "notes"]
        labels = {"user": "Member *", "copy": "Available book copy *", "due_date": "Due date *", "notes": "Notes (optional)"}
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"placeholder": "Condition of the copy or any extra notes..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only active, unblocked members may borrow; only copies on the shelf may be lent
        self.fields["user"].queryset = User.objects.filter(is_active=True, is_blocked=False).order_by("first_name", "last_name")
        self.fields["user"].label_from_instance = lambda u: f"{u.get_full_name() or u.email} - {u.email}"
        self.fields["user"].empty_label = "Choose a member"
        self.fields["copy"].queryset = (
            BookCopy.objects.filter(status=BookCopy.Status.AVAILABLE).select_related("book").order_by("book__title", "inventory_code"))
        self.fields["copy"].label_from_instance = lambda c: f"{c.inventory_code} - {c.book.title}"
        self.fields["copy"].empty_label = "Choose an available copy"
        today = timezone.localdate()
        self.fields["due_date"].initial = today + timedelta(days=14)                   # 14-day loan
        self.fields["due_date"].widget.attrs["min"] = (today + timedelta(days=1)).isoformat()
