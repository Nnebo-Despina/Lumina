# accounts/views.py
# Registration, login/logout, password recovery, password change and profiles
# for BOTH members and the administrator.

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, views as auth_views
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from .decorators import AdminRequiredMixin, MemberRequiredMixin, admin_required
from .forms import (
    AdminAuthenticationForm,
    AdminPasswordChangeForm,
    AdminPasswordResetForm,
    AdminProfileForm,
    EmailAuthenticationForm,
    LuminaPasswordChangeForm,
    LuminaSetPasswordForm,
    MemberPasswordResetForm,
    ProfileForm,
    RegisterForm,
)

# Shared by the two password-reset request pages (member + admin)
RESET_EMAIL = "accounts/emails/password_reset_email.txt"
RESET_SUBJECT = "accounts/emails/password_reset_subject.txt"


# =====================================================================
# MEMBER AREA
# =====================================================================
class RegisterView(CreateView):
    """One-time registration. Logged-in users are sent to their account."""

    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("library:account")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)          # saves the user (password is hashed)
        messages.success(self.request, "Your account has been created. Please log in.")
        return response


class LoginView(auth_views.LoginView):
    """Member login (blocked members are refused by the form)."""

    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True               # already logged in? skip the form

    def form_valid(self, form):
        response = super().form_valid(form)
        if not form.cleaned_data.get("remember"):
            self.request.session.set_expiry(0)       # session ends when the browser closes
        return response


class LogoutView(auth_views.LogoutView):
    """Logging out must be a POST (the nav 'Logout' button is a tiny form)."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "You have been logged out.")
        return response


class ForgotPasswordView(SuccessMessageMixin, auth_views.PasswordResetView):
    """Step 1: the member asks for a reset link.

    The same message is shown whether or not the email exists, so nobody can
    use this page to find out who is registered."""

    template_name = "accounts/forgot_password.html"
    form_class = MemberPasswordResetForm
    email_template_name = RESET_EMAIL
    subject_template_name = RESET_SUBJECT
    success_url = reverse_lazy("accounts:forgot_password")
    success_message = "If that email is registered, a reset link is on its way."


class ResetPasswordView(auth_views.PasswordResetConfirmView):
    """Step 2: the member opens the emailed link and chooses a new password."""

    template_name = "accounts/reset_password.html"
    form_class = LuminaSetPasswordForm
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Your password has been reset. Please log in.")
        return response


class ChangePasswordView(MemberRequiredMixin, SuccessMessageMixin, auth_views.PasswordChangeView):
    """A logged-in member changes their own password (the session stays valid)."""

    template_name = "accounts/change_password.html"
    form_class = LuminaPasswordChangeForm
    success_url = reverse_lazy("accounts:profile")
    success_message = "Your password has been changed."


class ProfileView(MemberRequiredMixin, SuccessMessageMixin, UpdateView):
    """A member views and edits their own details."""

    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")
    success_message = "Your profile has been updated."

    def get_object(self, queryset=None):
        return self.request.user                      # members can only ever edit themselves

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Real activity numbers for the summary card (models owned by other apps)
        context["books_read"] = user.reading_progress.count()
        context["downloads"] = user.download_logs.count()
        context["on_loan"] = user.book_issues.filter(status="issued").count()
        return context


# =====================================================================
# ADMINISTRATOR AREA   (/manage/...)
# =====================================================================
class AdminLoginView(auth_views.LoginView):
    """Administrator login: only is_staff accounts get through."""

    template_name = "manage/admin_login.html"
    authentication_form = AdminAuthenticationForm
    redirect_authenticated_user = False

    def get_default_redirect_url(self):
        return reverse("catalogue:manage_dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        if not form.cleaned_data.get("remember"):
            self.request.session.set_expiry(0)
        return response


class AdminForgotPasswordView(SuccessMessageMixin, auth_views.PasswordResetView):
    """Administrator password recovery (links are only sent to staff accounts)."""

    template_name = "manage/admin_forgot_password.html"
    form_class = AdminPasswordResetForm
    email_template_name = RESET_EMAIL
    subject_template_name = RESET_SUBJECT
    success_url = reverse_lazy("accounts:admin_forgot_password")
    success_message = "If that email belongs to an administrator, a reset link is on its way."


@admin_required
def admin_profile(request):
    """The administrator edits their details OR changes their password.

    The page holds two forms; the button that was pressed (save_profile or
    change_password) tells us which one to process."""
    profile_form = AdminProfileForm(instance=request.user)
    password_form = AdminPasswordChangeForm(request.user)

    if request.method == "POST":
        if "save_profile" in request.POST:
            profile_form = AdminProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile has been updated.")
                return redirect("accounts:admin_profile")

        elif "change_password" in request.POST:
            password_form = AdminPasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)   # keep the admin logged in
                messages.success(request, "Your password has been changed.")
                return redirect("accounts:admin_profile")

    return render(request, "manage/profile.html", {
        "profile_form": profile_form,
        "password_form": password_form,
    })
