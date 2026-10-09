# loans/models.py
# Physical book lending: one BookIssue row = one copy given to one member.

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from catalogue.models import BookCopy


class BookIssue(models.Model):
    class Status(models.TextChoices):
        ISSUED = "issued", "Issued"
        RETURNED = "returned", "Returned"

    # The member who borrowed the book (blocked / inactive members are not offered)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="book_issues",
        limit_choices_to={"is_active": True, "is_blocked": False},
    )

    # The physical copy that was handed over
    copy = models.ForeignKey(
        BookCopy,
        on_delete=models.PROTECT,
        related_name="issues",
    )

    # The staff member / admin who issued it
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="issued_books",
        limit_choices_to={"is_staff": True},
    )

    issued_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    returned_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ISSUED,
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-issued_at"]
        constraints = [
            # A copy can only have ONE active (not yet returned) issue at a time
            models.UniqueConstraint(
                fields=["copy"],
                condition=Q(status="issued"),
                name="one_active_issue_per_copy",
            ),
        ]

    def __str__(self):
        return f"{self.copy} - {self.user}"

    # ---------- derived information (not stored in the database) ----------

    @property
    def is_overdue(self):
        """True when the book is still out and the due date has passed."""
        return (
            self.status == self.Status.ISSUED
            and self.due_date < timezone.localdate()
        )

    @property
    def display_status(self):
        """'Overdue' is worked out on the fly; it is never saved."""
        return "Overdue" if self.is_overdue else self.get_status_display()

    # ---------- validation (runs in forms and the admin, NOT on plain save()) ----------

    def clean(self):
        errors = {}

        # Rules that only apply when the loan is first created
        if self._state.adding:
            if self.user_id and (self.user.is_blocked or not self.user.is_active):
                errors["user"] = "This member is blocked or inactive and cannot borrow books."

            if self.copy_id and self.copy.status != BookCopy.Status.AVAILABLE:
                errors["copy"] = "This copy is not available to borrow."

            if self.due_date and self.due_date <= timezone.localdate():
                errors["due_date"] = "The due date must be after today."

        if errors:
            raise ValidationError(errors)

    # ---------- keep the copy's status in step with the loan ----------

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            # A freshly issued copy is no longer on the shelf
            if (
                self.status == self.Status.ISSUED
                and self.copy.status != BookCopy.Status.ON_LOAN
            ):
                self.copy.status = BookCopy.Status.ON_LOAN
                self.copy.save(update_fields=["status"])

    def mark_returned(self):
        """Close the loan and put the copy back on the shelf."""
        if self.status == self.Status.RETURNED:
            return
        with transaction.atomic():
            self.status = self.Status.RETURNED
            self.returned_at = timezone.now()
            self.save()
            # Only free the copy if it was on loan (don't undo 'lost' or 'maintenance')
            if self.copy.status == BookCopy.Status.ON_LOAN:
                self.copy.status = BookCopy.Status.AVAILABLE
                self.copy.save(update_fields=["status"])