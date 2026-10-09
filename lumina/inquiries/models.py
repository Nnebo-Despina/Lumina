from django.db import models
from django.contrib.auth.models import User

class Inquiry(models.Model):

    SUBJECT_CHOICES = [
        ("general", "General"),
        ("nemberssip", "Membership"),
        ("request_book", "Request a book"),
        ("report_problem", "Report a problem"),

    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("answered", "Answered"),
    ]

    name = models.CharField(max_length=100)

    email = models.EmailField()

    subject = models.CharField(max_length=50,
    choices=SUBJECT_CHOICES
    )

    message = models.TextField()

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    answered_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name} - {self.subject}"

