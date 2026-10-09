from django.db import models
from django.contrib.auth.models import User

class Inquiry(models.Model):

    class Subject(models.TextChoices):
        GENERAL = "general", "General"
        MEMBERSHIP = "membership", "Membership"
        BOOK_REQUEST = "book_request", "Request a book"
        PROBLEM = "problem", "Report a problem"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ANSWERED = "answered", "Answered"

    name = models.CharField(max_length=100)

    email = models.EmailField()

    subject = models.CharField(max_length=50,
    choices = Subject.choices
    )

    message = models.TextField()

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries"
    )

    status = models.CharField(
        max_length=20,
        choices=Subject.choices,
        default=Status.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    answered_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.subject}: {self.email}"

