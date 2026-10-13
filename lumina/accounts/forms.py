# accounts/forms.py
# Every form used by the accounts app: login, register, profile and passwords.
#
# The widget "id" values (email, password, confirm ...) are set on purpose so
# they match the front-end HTML/JS: the show/hide password button and the
# "passwords must match" check in static/js/main.js look those ids up.

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    BaseUserCreationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.core.exceptions import ValidationError

from .decorators import BLOCKED_MESSAGE

User = get_user_model()


class TelInput(forms.TextInput):
    """<input type="tel"> (Django has no built-in phone widget)."""
    input_type = "tel"


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------
class EmailAuthenticationForm(AuthenticationForm):
    """Member login: email + password (+ 'remember me')."""

    # The field is still called "username" internally; it just holds the email
    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={
            "id": "email", "autofocus": True,
            "autocomplete": "username", "placeholder": "you@example.com",
        }),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "id": "password", "autocomplete": "current-password",
            "placeholder": "Your password",
        }),
    )
    remember = forms.BooleanField(required=False, label="Remember me")

    error_messages = {
        "invalid_login": "Incorrect email or password. Please try again.",
        "inactive": "This account is inactive.",
    }

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)           # rejects inactive accounts
        if user.is_blocked:                           # rejects blocked members
            raise ValidationError(BLOCKED_MESSAGE, code="blocked")


class AdminAuthenticationForm(EmailAuthenticationForm):
    """Administrator login: same as above, but the account must be staff."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError(
                "This account does not have administrator access.", code="not_staff"
            )


# ---------------------------------------------------------------------------
# REGISTER
# ---------------------------------------------------------------------------
class RegisterForm(BaseUserCreationForm):
    """One-time member registration."""

    terms = forms.BooleanField(
        label="I agree to the library rules and terms of use.",
        error_messages={"required": "You must accept the library rules to register."},
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "role")
        labels = {
            "first_name": "First name",
            "last_name": "Last name",
            "email": "Email address",
            "phone": "Phone (optional)",
            "role": "I am a",
        }
        widgets = {"phone": TelInput(attrs={"placeholder": "+234 ..."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        f = self.fields
        # ids used by the front-end script (main.js)
        f["first_name"].widget.attrs.update(id="first", autocomplete="given-name")
        f["last_name"].widget.attrs.update(id="last", autocomplete="family-name")
        f["email"].widget.attrs.update(id="email", autocomplete="username", placeholder="you@example.com")
        f["phone"].widget.attrs.update(id="phone")
        f["phone"].required = False
        f["role"].widget.attrs.update(id="role")
        f["password1"].label = "Password"
        f["password1"].widget.attrs.update(id="password", placeholder="At least 8 characters")
        f["password2"].label = "Confirm password"
        f["password2"].widget.attrs.update(id="confirm")
        f["terms"].widget.attrs.update(id="terms")
        f["password1"].help_text = ""      # the template shows its own short hint

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        # Case-insensitive duplicate check (Ada@x.com == ada@x.com)
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email


# ---------------------------------------------------------------------------
# PROFILE
# ---------------------------------------------------------------------------
class ProfileForm(forms.ModelForm):
    """A member edits their own details."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "role")
        labels = {
            "first_name": "First name",
            "last_name": "Last name",
            "email": "Email address",
            "phone": "Phone (optional)",
            "role": "I am a",
        }
        widgets = {"phone": TelInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["phone"].required = False
        self.fields["first_name"].widget.attrs["autocomplete"] = "given-name"
        self.fields["last_name"].widget.attrs["autocomplete"] = "family-name"
        self.fields["email"].widget.attrs["autocomplete"] = "email"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        # Another account may not already use this email
        clash = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if clash.exists():
            raise ValidationError("Another account already uses this email.")
        return email


class AdminProfileForm(ProfileForm):
    """The administrator's profile (no 'I am a' role) styled for the admin panel."""

    class Meta(ProfileForm.Meta):
        fields = ("first_name", "last_name", "email", "phone")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "field"


# ---------------------------------------------------------------------------
# PASSWORDS
# ---------------------------------------------------------------------------
class LuminaPasswordChangeForm(PasswordChangeForm):
    """Change password while logged in (member pages)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs.update(id="current")
        self.fields["new_password1"].widget.attrs.update(id="new-password", placeholder="At least 8 characters")
        self.fields["new_password2"].widget.attrs.update(id="confirm")
        self.fields["new_password1"].help_text = ""


class AdminPasswordChangeForm(LuminaPasswordChangeForm):
    """Same form, styled for the admin panel."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "field"
        # unique ids: the admin profile page also contains the details form
        self.fields["old_password"].widget.attrs["id"] = "cp"
        self.fields["new_password1"].widget.attrs["id"] = "np"
        self.fields["new_password2"].widget.attrs["id"] = "cf"


class MemberPasswordResetForm(PasswordResetForm):
    """Step 1 of recovery: ask for the email address."""

    email = forms.EmailField(
        label="Email address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            "id": "email", "autocomplete": "email", "placeholder": "you@example.com",
        }),
    )


class AdminPasswordResetForm(MemberPasswordResetForm):
    """Same, but a reset link is only sent to administrator accounts."""

    email = forms.EmailField(
        label="Admin email",
        max_length=254,
        widget=forms.EmailInput(attrs={
            "id": "email", "class": "field", "autocomplete": "email",
            "placeholder": "admin@lumina-library.example",
        }),
    )

    def get_users(self, email):
        return (user for user in super().get_users(email) if user.is_staff)


class LuminaSetPasswordForm(SetPasswordForm):
    """Step 2 of recovery: choose a new password from the emailed link."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].widget.attrs.update(id="password", placeholder="At least 8 characters")
        self.fields["new_password2"].widget.attrs.update(id="confirm")
        self.fields["new_password1"].help_text = ""
