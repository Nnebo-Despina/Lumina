# inquiries/forms.py

from django import forms

from .models import Inquiry


class ContactForm(forms.ModelForm):
    """The public 'Contact us' form (guests and members)."""

    class Meta:
        model = Inquiry
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
            "message": forms.Textarea(attrs={"placeholder": "How can we help?", "minlength": 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No blank "---------" choice: the subject starts on "General" (as in the original design)
        self.fields["subject"].choices = Inquiry.Subject.choices
        self.fields["subject"].initial = Inquiry.Subject.GENERAL

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Please write at least 10 characters.")
        return message
